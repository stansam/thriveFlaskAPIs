from app.models import Payment, Booking
from app.models.enums import PaymentStatus, BookingStatus
from app.extensions import db
from sqlalchemy.orm import Session
from app.repository.finance.exceptions import FinanceServiceError, PaymentFailed
import logging

logger = logging.getLogger(__name__)

class VerifyPayment:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, booking_id: str, verified: bool, rejection_reason: str = None) -> Payment:
        try:
            booking = self.db.get(Booking, booking_id)
            if not booking:
                raise FinanceServiceError("Booking not found")

            # Find the pending payment
            payment = self.db.query(Payment).filter_by(
                booking_id=booking_id, 
                status=PaymentStatus.PENDING
            ).first()
            
            if not payment:
                 # It might be in PARTIAL or another state, but for this flow we expect PENDING.
                 # If no payment record exists, we can't verify it.
                 raise FinanceServiceError("No pending payment found for this booking")

            if verified:
                payment.status = PaymentStatus.PAID
                booking.status = BookingStatus.CONFIRMED
                # TODO: Trigger email "Payment Received / Booking Confirmed"
            else:
                payment.status = PaymentStatus.FAILED
                booking.status = BookingStatus.FAILED # Or keep it AWAITING and ask for retry? 
                # Plan says: If Rejected: Status -> PAYMENT_FAILED (PaymentStatus)
                # Plan says: Notify User ("Invalid Proof").
                # Let's verify what BookingStatus should be. 
                # If payment fails, booking might be FAILED or back to PENDING.
                # Let's set booking to FAILED for now as it's a rejection of the request.
                booking.status = BookingStatus.FAILED
            
            self.db.commit()
            self.db.refresh(payment)
            return payment

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error verifying payment: {e}")
            raise FinanceServiceError(f"Failed to verify payment: {str(e)}")
