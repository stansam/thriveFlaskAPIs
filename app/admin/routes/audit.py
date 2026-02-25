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
             page = request.args.get('page', 1, type=int)
             limit = request.args.get('limit', 50, type=int)
             
             from app.repository import repositories
             paginated_data = repositories.audit_log.get_recent_logs(page=page, limit=limit)
             
             # Tracking the action inherently observing the logs mapping naturally
             log_audit(
                 action=AuditAction.VIEW,
                 entity_type=EntityType.AUDIT_LOG,
                 entity_id=None,
                 user_id=current_user.id,
                 description=f"Global Admin fetched compliance trail traces structurally (Page {page})."
             )
             
             return jsonify({
                 "items": [log.to_dict() for log in paginated_data["items"]],
                 "total": paginated_data["total"],
                 "pages": paginated_data["pages"],
                 "current_page": paginated_data["current_page"],
                 "has_next": paginated_data["has_next"],
                 "has_prev": paginated_data["has_prev"]
             }), 200

        except Exception as e:
             logger.error(f"Compliance ledger extract failure: {e}")
             return jsonify({"error": str(e)}), 500
