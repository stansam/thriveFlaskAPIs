from typing import Optional
from datetime import datetime, timezone
from app.models.payment import Invoice, Payment
from app.models.booking import Booking
from app.models.enums import PaymentStatus, InvoiceStatus
from app.repository import repositories
from app.dto.payment.schemas import GenerateInvoiceDTO, SubmitPaymentProofDTO, VerifyPaymentDTO
from app.services.payment.utils import generate_invoice_number

class PaymentService:
    """
    PaymentService oversees the orchestration of explicit Invoice generation and
    the manual workflow of ingesting user payment proofs and executing administrative reconciliations.
    """

    def __init__(self):
        self.invoice_repo = repositories.invoice
        self.payment_repo = repositories.payment
        self.booking_repo = repositories.booking
        self.user_repo = repositories.user

    def generate_invoice(self, payload: GenerateInvoiceDTO) -> Invoice:
        """
        Creates a uniquely tracked ledger invoice record securely tied to the User
        and potentially a deeper target (Booking/Subscription) for audit trails.
        """
        user = self.user_repo.get_by_id(payload.user_id)
        if not user:
            raise ValueError("Invalid user assigned to invoice request.")

        from datetime import timedelta
        # Assign + 7 days strictly mimicking physical accounts receivable timelines
        issued = datetime.now(timezone.utc).date()
        due = issued + timedelta(days=7)

        return self.invoice_repo.create({
            "user_id": user.id,
            "booking_id": payload.booking_id,
            "subscription_id": payload.subscription_id,
            "invoice_number": generate_invoice_number(),
            "issued_date": issued,
            "due_date": due,
            "total_amount": payload.amount,
            "currency": payload.currency,
            "status": InvoiceStatus.ISSUED
        }, commit=True)

    def submit_payment_proof(self, payload: SubmitPaymentProofDTO) -> Payment:
        """
        Handles the offline processing step where clients upload bank transfer
        receipts/references indicating they have fulfilled the generated invoice limits natively.
        """
        booking = self.booking_repo.get_by_id(payload.booking_id)
        if not booking:
            raise ValueError("Target checkout booking does not exist.")
            
        # Optional: Grab explicit Invoice linked to Booking natively to match exact amount requirements
        invoices = self.invoice_repo.get_invoices_by_booking_id(booking.id)
        amount_due = sum(inv.total_amount for inv in invoices) if invoices else 0.0
        
        # Build the exact `Payment` transaction mimicking a stripe processing lock:
        return self.payment_repo.create({
            "booking_id": booking.id,
            "user_id": booking.user_id,
            "amount": amount_due,
            "currency": "USD",
            "payment_method": payload.payment_method,
            "transaction_id": payload.transaction_id, # Safely mapped external ref code
            "payment_proof_url": payload.payment_proof_url,
            "status": PaymentStatus.PENDING,
            "payment_date": datetime.now(timezone.utc)
        }, commit=True)

    def verify_payment(self, payload: VerifyPaymentDTO, admin_user_id: str) -> Payment:
        """
        The critical Reconciliation boundary where a corporate admin maps the physical bank
        clearing securely shifting the state bounds towards CONFIRMED freeing tickets downstream.
        """
        payment = self.payment_repo.get_by_id(payload.payment_id)
        if not payment:
             raise ValueError("Payment transaction ledger record not found.")
             
        # TODO: Safely write AuditLog bounds indicating `admin_user_id` executed this transition
        
        updates_dict = {"status": payload.status}
        validated_payment = self.payment_repo.update(payment.id, updates_dict, commit=True)
        
        if payload.status == PaymentStatus.COMPLETED:
             # Force underlying Invoices mappings closed explicitly natively
             invoices = self.invoice_repo.get_invoices_by_booking_id(payment.booking_id)
             for inv in invoices:
                  self.invoice_repo.update(inv.id, {"status": InvoiceStatus.PAID}, commit=True)
                  
             # Force Booking fulfillment internally (Mock mapping towards `BookingService` eventually)
             # E.g. trigger NotificationService("PAYMENT_SUCCESS") 
             
        return validated_payment
