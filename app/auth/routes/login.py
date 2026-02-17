from flask import request, jsonify
from flask.views import MethodView
from flask_login import login_user
from app.auth.schemas.login import LoginSchema
from app.extensions import db
from app.repository.user.services import UserService
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class Login(MethodView):
    def post(self):
        schema = LoginSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        service = UserService(db.session)
        user = service.authenticate_user(data['email'], data['password'])

        if user:
            login_user(user, remember=data.get('remember_me', False))
            
            log_audit(
                action=AuditAction.LOGIN,
                entity_type=EntityType.USER,
                entity_id=user.id,
                user_id=user.id,
                description=f"User {user.email} logged in."
            )
            track_metric(metric_name="login_success", category="auth")
            
            return jsonify({
                "message": "Login successful",
                "user": user.to_dict()
            }), 200
        
        track_metric(metric_name="login_failure", category="auth")
        logger.warning(f"Failed login attempt for {data.get('email')}")
        
        return jsonify({"message": "Invalid email or password"}), 401