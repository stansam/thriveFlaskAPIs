import logging
from flask import jsonify, request
from flask.views import MethodView
from app.admin.routes.dashboard import admin_required
from app.admin.schemas.companies import CompanyStatusSchema
from marshmallow import ValidationError
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType
from flask_login import current_user
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO

logger = logging.getLogger(__name__)

class CompanyListView(MethodView):
    decorators = [admin_required]

    def get(self):
        from app.repository import repositories
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        paginated_data = repositories.company.get_all_companies(page=page, limit=limit)
        
        return jsonify({
            "items": [c.to_dict() for c in paginated_data["items"]],
            "total": paginated_data["total"],
            "pages": paginated_data["pages"],
            "current_page": paginated_data["current_page"],
            "has_next": paginated_data["has_next"],
            "has_prev": paginated_data["has_prev"]
        }), 200


class CompanyStatusView(MethodView):
    decorators = [admin_required]

    def put(self, company_id):
        schema = CompanyStatusSchema()
        try:
             data = schema.load(request.json)
        except ValidationError as err:
             return jsonify(err.messages), 400

        from app.repository import repositories
        company = repositories.company.find_by_id(company_id)
        if not company:
             return jsonify({"error": "Global B2B entity not found natively."}), 404

        try:
             # TODO: Check if repository has a direct update mechanism or service
             company.is_active = data['is_active']
             from app.extensions import db
             db.session.commit()
             
             action_desc = "Re-Activated" if data['is_active'] else "Suspended"
             
             log_audit(
                 action=AuditAction.UPDATE,
                 entity_type=EntityType.COMPANY,
                 entity_id=company.id,
                 user_id=current_user.id,
                 description=f"Admin {action_desc} Corporate B2B Account struct natively."
             )
             track_metric("company_status_changed", category="admin")
             
             try:
                 ns = NotificationService()
                 
                 company_admin = repositories.user.get_company_admin(company_id)
                 if company_admin:
                     ns.dispatch_notification(DispatchNotificationDTO(
                         user_id=company_admin.id,
                         trigger_event="COMPANY_STATUS_CHANGED",
                         context={"is_active": data['is_active'], "company_name": company.name}
                     ))
             except Exception as notif_err:
                 logger.error(f"Failing mapping B2B status dispatch: {notif_err}")

             return jsonify({
                 "message": f"Corporate account securely {action_desc}."
             }), 200

        except Exception as e:
             logger.error(f"Error mapping corporate status: {e}")
             return jsonify({"error": str(e)}), 500
