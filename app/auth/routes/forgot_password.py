import logging
from flask import request, jsonify
from flask.views import MethodView
from marshmallow import ValidationError
from app.auth.schemas.forgot_password import ForgotPasswordSchema
from app.services.auth.service import AuthService
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO
from app.utils.analytics import track_metric

logger = logging.getLogger(__name__)

class ForgotPassword(MethodView):
    def post(self):
        schema = ForgotPasswordSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        auth_service = AuthService()
        
        # We process the lookup securely avoiding returning physical Hints to attacker bots
        auth_service.request_password_reset(data['email'])
        track_metric(metric_name="password_reset_requested", category="auth")
        
        # In this workflow `AuthService` sets the token. We need the physical user context 
        # to trigger the notification cleanly if found. 
        # Since AuthService explicitly returns True always, we query the user quickly here 
        # to assemble the link precisely for the immediate payload dispatch 
        # (This avoids polluting AuthService with request parsing)
        from app.repository import repositories
        user = repositories.user.find_by_email(data['email'])
        
        if user and user.email_verification_token:
             ns = NotificationService()
             reset_link = f"{request.host_url}api/auth/reset-password?token={user.email_verification_token}"
             try:
                 ns.dispatch_notification(DispatchNotificationDTO(
                     user_id=user.id,
                     trigger_event="PASSWORD_RESET_REQUESTED",
                     context={
                         "first_name": user.first_name,
                         "reset_link": reset_link
                     }
                 ))
             except Exception as e:
                 logger.error(f"Failed to dispatch password reset email bounded: {e}")

        # Always return generically masking the true internal hit evaluation.
        return jsonify({
            "message": "If that email is registered, you will receive a password reset link shortly."
        }), 200
