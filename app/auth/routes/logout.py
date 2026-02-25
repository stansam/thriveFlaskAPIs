import logging
from flask import jsonify
from flask.views import MethodView
from flask_login import logout_user, current_user
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType

logger = logging.getLogger(__name__)

class Logout(MethodView):
    def post(self):
        if not current_user.is_authenticated:
            return jsonify({"message": "Already logged out."}), 200
            
        user_id = current_user.id
        
        logout_user()
        
        track_metric(metric_name="user_logged_out", category="auth")
        log_audit(
            action=AuditAction.LOGOUT,
            entity_type=EntityType.USER,
            entity_id=user_id,
            user_id=user_id,
            description="User terminated secure session."
        )
        
        return jsonify({"message": "Successfully logged out."}), 200