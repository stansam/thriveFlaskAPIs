import logging
from flask import request, jsonify
from flask.views import MethodView
from marshmallow import ValidationError
from app.auth.schemas.register import RegisterSchema
from app.dto.auth.schemas import RegisterRequestDTO
from app.services.auth.service import AuthService
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType, UserRole

logger = logging.getLogger(__name__)

class Register(MethodView):
    def post(self):
        schema = RegisterSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        auth_service = AuthService()
        
        # Explicit DTO reconstruction enforcing typing boundaries
        payload = RegisterRequestDTO(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=data['password'],
            phone=data.get('phone'),
            role=UserRole.CLIENT,
            gender=data.get('gender'),
            locale=data.get('locale'),
            company_id=data.get('company_id')
        )
        
        try:
            user = auth_service.register_user(payload)
            
            log_audit(
                action=AuditAction.CREATE,
                entity_type=EntityType.USER,
                entity_id=user.id,
                user_id=user.id, 
                description="New user successfully registered."
            )
            track_metric(metric_name="user_registered", category="auth")
            
            # Initiate background notification natively
            try:
                ns = NotificationService()
                verification_link = f"{request.host_url}api/auth/verify-email?token={user.email_verification_token}"
                ns.dispatch_notification(DispatchNotificationDTO(
                    user_id=user.id,
                    trigger_event="ACCOUNT_VERIFICATION",
                    context={
                        "first_name": user.first_name,
                        "verification_link": verification_link
                    }
                ))
            except Exception as email_err:
                logger.error(f"Failed dispatching welcome verification notification: {email_err}")

            return jsonify({
                "message": "Registration successful. Please check your email to verify your account.",
                "user": user.to_dict()
            }), 201

        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            logger.error(f"Registration unhandled fault: {e}")
            return jsonify({"error": "An internal server error occurred processing registration."}), 500
