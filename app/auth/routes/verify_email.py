from flask import request, jsonify
from flask.views import MethodView
from app.auth.schemas.verify_email import VerifyEmailSchema
from app.extensions import db
from app.repository.user.services import UserService
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.utils.email import send_verification_email
from app.models.enums import AuditAction, EntityType
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class VerifyEmail(MethodView):
    def post(self):
        schema = VerifyEmailSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        try:
            token = data['token']
            user_id = request.json.get('user_id')
            
            if not user_id:
                return jsonify({"user_id": ["Missing data for required field."]}), 400

            service = UserService(db.session)
            user = service.VerifyUserEmail(user_id, token)
            
            # Audit & Analytics
            log_audit(
                action=AuditAction.UPDATE,
                entity_type=EntityType.USER,
                entity_id=user.id,
                user_id=user.id,
                description=f"User {user.email} verified email."
            )
            track_metric(metric_name="email_verified", category="auth")

            return jsonify({
                "message": "Email verified successfully.",
                "user": user.to_dict()
            }), 200
            
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            return jsonify({"message": str(e)}), 400

class ResendVerification(MethodView):
    def post(self):
        email = request.json.get('email')
        if not email:
             return jsonify({"email": ["Email is required."]}), 400

        user_service = UserService(db.session)
        try:
            user = user_service.GetUserByEmail(email)
            if user:
                if user.email_verified:
                    return jsonify({"message": "Email is already verified."}), 400
                
                user = user_service.GenerateEmailVerificationToken(user.id)
                db.session.commit() 
                
                send_verification_email(user, user.email_verification_token)
                
                track_metric(metric_name="verification_resend_requested", category="auth")
                logger.info(f"Verification email resend requested for {email}")
            
            return jsonify({"message": "If this email is registered and unverified, you will receive a verification link."}), 200
            
        except Exception as e:
             logger.error(f"Resend verification failed: {e}")
             return jsonify({"message": "An error occurred"}), 500
