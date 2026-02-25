from flask import request, jsonify, current_app
from flask.views import MethodView
from app.auth.schemas.reset_password import ResetPasswordSchema
from app.extensions import db
from app.services.user.service import UserService
from app.utils.email import send_password_reset_email
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType
from app.repository import repositories
from marshmallow import ValidationError
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import logging

logger = logging.getLogger(__name__)

def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


class ForgotPassword(MethodView):
    def post(self):
        email = request.json.get('email')
        if not email:
            return jsonify({"email": ["Email is required."]}), 400
            
        try:
            # We directly hit the repository for user lookups bypassing deprecated exceptions
            user = repositories.user.find_by_email(email)

            if user:
                serializer = get_serializer()
                token = serializer.dumps(user.email, salt='password-reset-salt')
                
                send_password_reset_email(user, token)
                
                track_metric(metric_name="password_reset_requested", category="auth")
                logger.info(f"Password reset requested for {email}")
            else:
                 logger.info(f"Password reset requested for non-existent email {email}")

            return jsonify({"message": "If this email is registered, you will receive a reset link."}), 200

        except Exception as e:
            logger.error(f"Error in ForgotPassword: {e}")
            return jsonify({"message": "An error occurred"}), 500

class ResetPassword(MethodView):
    def post(self):
        schema = ResetPasswordSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400
            
        token = data['token']
        new_password = data['new_password']
        
        try:
            serializer = get_serializer()
            email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
            
            user = repositories.user.find_by_email(email)
            if not user:
                 return jsonify({"message": "Invalid token or user not found."}), 400
                 
            user.set_password(new_password)
            repositories.user.update(user.id, {"password_hash": user.password_hash}, commit=True)
            
            log_audit(
                action=AuditAction.UPDATE,
                entity_type=EntityType.USER,
                entity_id=user.id,
                user_id=user.id,
                description="User reset their password via email link."
            )
            track_metric(metric_name="password_reset_success", category="auth")
            
            return jsonify({"message": "Password has been reset successfully."}), 200
            
        except SignatureExpired:
            return jsonify({"message": "The reset token has expired."}), 400
        except BadSignature:
            return jsonify({"message": "Invalid reset token."}), 400
        except Exception as e:
            logger.error(f"Error in ResetPassword: {e}")
            return jsonify({"message": "An error occurred"}), 500
