import logging
from flask import request, jsonify
from flask.views import MethodView
from marshmallow import ValidationError
from app.admin.routes.dashboard import admin_required
from app.admin.schemas.payments import VerifyPaymentSchema
from app.services.payment.service import PaymentService
from app.dto.payment.schemas import VerifyPaymentDTO
from app.models.enums import PaymentStatus, AuditAction, EntityType
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from flask_login import current_user
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO

logger = logging.getLogger(__name__)

class VerifyPaymentView(MethodView):
    decorators = [admin_required]

    def post(self, booking_id):
        schema = VerifyPaymentSchema()
        try:
             data = schema.load(request.json)
        except ValidationError as err:
             return jsonify(err.messages), 400
             
        finance_service = PaymentService()
        
        mapped_status = PaymentStatus.PAID if data['status'] == 'approved' else PaymentStatus.FAILED
        
        dto = VerifyPaymentDTO(
             payment_id=booking_id,
             status=mapped_status,
             admin_notes=data.get('rejection_reason')
        )

        try:
             payment = finance_service.verify_payment(dto, current_user.id)
             
             log_audit(
                 action=AuditAction.UPDATE,
                 entity_type=EntityType.PAYMENT,
                 entity_id=payment.id,
                 user_id=current_user.id,
                 description=f"Admin structurally evaluated offline wire mapping to: {payment.status.value}"
             )
             
             track_metric("payment_reconciled", category="admin", value=payment.amount)
             
             try:
                 ns = NotificationService()
                 
                 from app.repository import repositories
                 booking = repositories.booking.find_by_id(payment.booking_id)
                 
                 event = "PAYMENT_CONFIRMED" if payment.status == PaymentStatus.PAID else "PAYMENT_REJECTED"
                 ns.dispatch_notification(DispatchNotificationDTO(
                     user_id=booking.user_id,
                     trigger_event=event,
                     context={"rejection_reason": data.get('rejection_reason', 'N/A')}
                 ))
             except Exception as notif_err:
                 logger.error(f"Failing mapping wire verification downstream: {notif_err}")

             return jsonify({
                 "message": f"Payment successfully locked to {payment.status.value}.",
                 "payment": payment.to_dict()
             }), 200

        except Exception as e:
             logger.error(f"Offline verify error mapping: {e}")
             return jsonify({"error": str(e)}), 400
