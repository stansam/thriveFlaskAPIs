import logging
from flask import request, jsonify
from flask.views import MethodView
from marshmallow import ValidationError
from app.auth.schemas.verify_email import VerifyEmailSchema
from app.services.auth.service import AuthService
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType

logger = logging.getLogger(__name__)

class VerifyEmail(MethodView):
    def post(self):
        # Allow token ingestion via JSON body or URL Query explicitly
        token = request.args.get('token') or (request.json or {}).get('token')
        
        schema = VerifyEmailSchema()
        try:
            data = schema.load({'token': token} if token else request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        auth_service = AuthService()
        success = auth_service.verify_email(data['token'])
        
        if success:
            # Note: The raw physical DB model lacks the `user_id` context directly returned from verify_email True/False
            # If explicit Audit logging is requested, the AuthService API should be adjusted to return `user` object.
            # Assuming basic tracking:
            track_metric(metric_name="email_verified", category="auth")
            
            return jsonify({"message": "Email successfully verified!"}), 200
            
        logger.warning("Failed email verification attempt explicitly triggering bounds.")
        return jsonify({"error": "Invalid or expired verification token."}), 400
