from app.services.payment.service import PaymentService
from app.services.notification.service import NotificationService
from app.dto.payment.schemas import GenerateInvoiceDTO, SubmitPaymentProofDTO, VerifyPaymentDTO
from app.dto.notification.schemas import DispatchNotificationDTO, SendEmailDTO
from app.models.enums import PaymentMethod, PaymentStatus

print("Imports successful!")
svc1 = PaymentService()
svc2 = NotificationService()

dto1 = GenerateInvoiceDTO(user_id="123", amount=150.00, booking_id="456")
dto2 = SubmitPaymentProofDTO(booking_id="456", payment_method=PaymentMethod.BANK_TRANSFER, payment_proof_url="http://s3/receipt.pdf")
dto3 = DispatchNotificationDTO(user_id="123", trigger_event="PAYMENT_RECEIVED", context={"name": "John"})

print("Instantiations successful! DTOs constructed properly.")
