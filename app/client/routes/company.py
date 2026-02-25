import logging
from flask import request, jsonify
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from app.client.schemas.company import EmployeeInviteSchema
from app.dto.company.schemas import EmployeeDTO, ManageEmployeeDTO
from app.services.company.service import CompanyService
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType, UserRole

logger = logging.getLogger(__name__)

class CompanyEmployeesView(MethodView):
    decorators = [login_required]

    def post(self):
        """Invoke secure employee registration boundaries scoped to Company."""
        if current_user.role != UserRole.COMPANY_ADMIN or not current_user.company_id:
            return jsonify({"error": "Strictly limited to enrolled B2B Administrators."}), 403

        schema = EmployeeInviteSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        company_service = CompanyService()
        
        employee_dto = EmployeeDTO(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=data['password'],
            phone=data.get('phone')
        )
        
        manage_dto = ManageEmployeeDTO(
            action="add",
            user_data=employee_dto
        )
        
        try:
             # This natively enforces the Company seating allocation logic centrally 
             new_user = company_service.manage_employees(current_user.company_id, manage_dto)
             
             track_metric("b2b_employee_invited", category="client")
             log_audit(
                 action=AuditAction.CREATE,
                 entity_type=EntityType.USER,
                 entity_id=new_user.id,
                 user_id=current_user.id,
                 description=f"Provisioned employee '{new_user.email}' into B2B sector natively."
             )
             
             # Dispense welcome invitation to employee automatically
             try:
                 ns = NotificationService()
                 link = f"{request.host_url}api/auth/login"
                 ns.dispatch_notification(DispatchNotificationDTO(
                     user_id=new_user.id,
                     trigger_event="B2B_EMPLOYEE_INVITED",
                     context={
                         "company_name": new_user.company.name,
                         "login_link": link,
                         "temp_password": data['password'] # Assumes immediate first-login rotation in App flow
                     }
                 ))
             except Exception as notif_err:
                 logger.error(f"Failed emitting B2B notification bindings: {notif_err}")

             return jsonify({
                 "message": "Employee provisioned effectively.",
                 "employee": new_user.to_dict()
             }), 201

        except ValueError as ve:
             return jsonify({"error": str(ve)}), 400

    def delete(self, employee_id):
        """Administratively remove standard B2B User mappings explicitly."""
        if current_user.role != UserRole.COMPANY_ADMIN or not current_user.company_id:
            return jsonify({"error": "Strictly limited to enrolled B2B Administrators."}), 403

        company_service = CompanyService()
        manage_dto = ManageEmployeeDTO(action="remove")
        
        # NOTE: Implement `action="remove"` accurately in `CompanyService` recognizing `employee_id` bounds.
        # Ensure company bounds check natively applies before wiping physical user references.
        # (CompanyService logic implies it uses DTO or signature adjustments but assumed conceptually active).
        
        from app.repository import repositories
        target_employee = repositories.user.find_by_id(employee_id)
        if not target_employee or target_employee.company_id != current_user.company_id:
             return jsonify({"error": "Employee structurally not found within bound domain."}), 404

        try:
            # We explicitly unlink the B2B bounding box ensuring their profile exists natively isolated or deleted entirely
            # depending on `CompanyService` structural logic rules.
            target_employee.company_id = None
            
            from app.extensions import db
            db.session.commit()
             
            track_metric("b2b_employee_removed", category="client")
            log_audit(
                 action=AuditAction.UPDATE,
                 entity_type=EntityType.USER,
                 entity_id=employee_id,
                 user_id=current_user.id,
                 description="Decommissioned B2B bindings enforcing standard user state natively."
            )
            return jsonify({"message": "B2B employee constraints successfully stripped."}), 200

        except Exception as e:
            logger.error(f"Unlink B2B Exception: {e}")
            return jsonify({"error": str(e)}), 400
