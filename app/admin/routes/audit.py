import logging
from flask import jsonify, request
from flask.views import MethodView
from app.admin.routes.dashboard import admin_required
from app.utils.audit_log import log_audit
from app.models.enums import AuditAction, EntityType
from flask_login import current_user

logger = logging.getLogger(__name__)

class AuditLogView(MethodView):
    decorators = [admin_required]

    def get(self):
        """Fetch strict chronological security ledger."""
        try:
             limit = int(request.args.get('limit', 50))
             
             from app.repository import repositories
             logs = repositories.audit_log.get_recent_logs(limit=limit)
             
             # Tracking the action inherently observing the logs mapping naturally
             log_audit(
                 action=AuditAction.VIEW,
                 entity_type=EntityType.AUDIT_LOG,
                 entity_id=None,
                 user_id=current_user.id,
                 description="Global Admin fetched compliance trail traces structurally."
             )
             
             return jsonify({
                 "logs": [log.to_dict() for log in logs]
             }), 200

        except Exception as e:
             logger.error(f"Compliance ledger extract failure: {e}")
             return jsonify({"error": str(e)}), 500
