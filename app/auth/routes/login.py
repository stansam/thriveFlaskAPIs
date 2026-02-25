import logging
from flask import request, jsonify
from flask.views import MethodView
from marshmallow import ValidationError
from app.auth.schemas.login import LoginSchema
from app.dto.auth.schemas import LoginRequestDTO
from app.services.auth.service import AuthService
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType

logger = logging.getLogger(__name__)

class Login(MethodView):
    def post(self):
        schema = LoginSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        auth_service = AuthService()
        payload = LoginRequestDTO(
            email=data['email'],
            password=data['password'],
            remember=data.get('remember_me', False)
        )
        
        success, user = auth_service.login_user(payload)

        if success and user:
            log_audit(
                action=AuditAction.LOGIN,
                entity_type=EntityType.USER,
                entity_id=user.id,
                user_id=user.id,
                description="User successfully authenticated."
            )
            track_metric(metric_name="login_success", category="auth")
            
            return jsonify({
                "message": "Login successful",
                "user": user.to_dict()
            }), 200
        
        track_metric(metric_name="login_failed", category="auth")
        logger.warning(f"Failed login attempt for {data.get('email')}")
        
        return jsonify({"error": "Invalid email or password"}), 401