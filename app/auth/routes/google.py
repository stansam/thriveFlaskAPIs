from flask import request, jsonify
from flask.views import MethodView
from flask_login import login_user
from app.auth.schemas.google import GoogleOAuthSchema
from app.extensions import db
from app.services.user.service import UserService
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class Google(MethodView):
    def post(self):
        schema = GoogleOAuthSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        user_service = UserService(db.session)
        try:
            user = user_service.google_oauth(data['id_token'])
            
            if user:
                login_user(user, remember=data.get('remember_me', False))
                
                log_audit(
                    action=AuditAction.LOGIN,
                    entity_type=EntityType.USER,
                    entity_id=user.id,
                    user_id=user.id,
                    description=f"User {user.email} logged in via Google."
                )
                track_metric(metric_name="login_google_success", category="auth", dimension_key="google")
                
                return jsonify({
                    "message": "Google login successful",
                    "user": user.to_dict()
                }), 200
            else:
                track_metric(metric_name="login_google_failure", category="auth", dimension_key="google")
                return jsonify({"message": "Google authentication failed"}), 401
                
        except Exception as e:
            logger.error(f"Google login error: {e}")
            track_metric(metric_name="login_google_error", category="auth", dimension_key="google")
            return jsonify({"message": str(e)}), 400