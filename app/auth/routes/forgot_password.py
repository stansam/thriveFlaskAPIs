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
        
        # Always return generically masking the true internal hit evaluation.
        return jsonify({
            "message": "If that email is registered, you will receive a password reset link shortly."
        }), 200
