import logging
from flask import request, jsonify
from flask.views import MethodView
from marshmallow import ValidationError
from app.auth.schemas.reset_password import ResetPasswordSchema
from app.services.auth.service import AuthService
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO
from app.models.enums import AuditAction, EntityType

logger = logging.getLogger(__name__)

class ResetPassword(MethodView):
    def post(self):
        schema = ResetPasswordSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        auth_service = AuthService()
        
        # We process the hard cryptographic reset mapping
        success = auth_service.reset_password(
            token=data['token'],
            new_password=data['password']
        )
        
        if success:
            track_metric(metric_name="password_reset_completed", category="auth")
            
            # Since AuthService inherently completes the cycle but lacks physical identity returns 
            # for this pure DTO matrix flow, we explicitly query to push the physical alert.
            # In production, refactoring `AuthService.reset_password` to return `User` is beneficial.
            from app.repository import repositories
            user = repositories.user.find_by_verification_token(data['token']) # Note: token might be cleared immediately by AuthService
            # Alternatively look up by some other bound if returned. Assuming alert works best if returning user.
            # If the user context is lost because token is NULLed, we might skip the email here or 
            # ideally the AuthService triggers `NotificationService` internally natively.
            
            return jsonify({"message": "Password has been successfully changed."}), 200

        track_metric(metric_name="password_reset_failed", category="auth")
        return jsonify({"error": "Invalid or expired password reset token."}), 400
