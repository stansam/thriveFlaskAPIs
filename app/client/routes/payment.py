import logging
from flask import request, jsonify
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from app.client.schemas.payment import InvoicePaymentSchema
from app.dto.payment.schemas import SubmitPaymentProofDTO
from app.services.payment.service import PaymentService
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO

logger = logging.getLogger(__name__)

class InvoicePaymentView(MethodView):
    decorators = [login_required]

    def post(self, invoice_number):
        schema = InvoicePaymentSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        # Retrieve explicit mapping to verify Booking linkage
        from app.repository import repositories
        invoice = repositories.invoice.find_by_invoice_number(invoice_number)
        
        if not invoice:
            return jsonify({"error": "Invoice not found."}), 404
            
        # Assert the invoice strictly belongs to the current user's bound resources
        # We lookup the booking explicitly ensuring the identity graph connects
        booking = repositories.booking.find_by_id(invoice.booking_id)
        if booking.user_id != current_user.id:
            return jsonify({"error": "Unauthorized assignment."}), 403

        payment_service = PaymentService()
        payload = SubmitPaymentProofDTO(
            booking_id=booking.id,
            payment_method=data['payment_method'],
            payment_proof_url=data['payment_proof_url'],
            transaction_id=data.get('transaction_id')
        )
        
        try:
             payment = payment_service.submit_payment_proof(payload)
             track_metric("payment_proof_submitted", category="client", value=invoice.amount)
             log_audit(
                 action=AuditAction.CREATE,
                 entity_type=EntityType.PAYMENT,
                 entity_id=payment.id,
                 user_id=current_user.id,
                 description=f"Automated proof submission tracking against '{invoice.invoice_number}'."
             )
             
             try:
                 ns = NotificationService()
                 
                 # Send alert to User natively confirming receipt
                 ns.dispatch_notification(DispatchNotificationDTO(
                     user_id=current_user.id,
                     trigger_event="PAYMENT_RECEIVED",
                     context={"invoice_number": invoice.invoice_number}
                 ))
                 
                 # Emulate escalating the receipt bound physically towards the Admin Queue
                 admin = repositories.user.get_admin_user()
                 if admin:
                    ns.dispatch_notification(DispatchNotificationDTO(
                        user_id=admin.id,
                        trigger_event="PAYMENT_PENDING_VERIFICATION",
                        context={"invoice_number": invoice.invoice_number, "client_email": current_user.email}
                    ))
             except Exception as notif_err:
                 logger.error(f"Failed dispatching payment notifications: {notif_err}")

             return jsonify({
                 "message": "Payment proof explicitly received. Esculated to Admin verification.",
                 "payment": payment.to_dict()
             }), 201

        except ValueError as ve:
             return jsonify({"error": str(ve)}), 400
