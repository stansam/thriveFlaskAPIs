from app.models import Payment, Booking
from app.models.enums import PaymentStatus, BookingStatus, PaymentMethod
from app.extensions import db
from sqlalchemy.orm import Session
from app.repository.finance.exceptions import FinanceServiceError
import logging

logger = logging.getLogger(__name__)

class RecordPaymentProof:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, booking_id: str, receipt_url: str, payment_method: str = "manual_transfer") -> Payment:
        try:
            booking = self.db.get(Booking, booking_id)
            if not booking:
                raise FinanceServiceError("Booking not found")

            # Check if a payment record already exists for this booking (for this method)
            # or allow multiple? simpler to find one pending/partial or create new.
            
            payment = self.db.query(Payment).filter_by(
                booking_id=booking_id, 
                status=PaymentStatus.PENDING
            ).first()

            if not payment:
                # Create a new payment record representing this attempt
                # We might not know the exact amount if it's a partial payment proof, 
                # but typically it's for the full booking amount.
                payment = Payment(
                    booking_id=booking_id,
                    user_id=booking.user_id,
                    amount=booking.total_amount,
                    currency=booking.currency,
                    payment_method=PaymentMethod(payment_method),
                    status=PaymentStatus.PENDING,
                    receipt_url=receipt_url
                )
                self.db.add(payment)
            else:
                # Update existing
                payment.receipt_url = receipt_url
                payment.payment_method = PaymentMethod(payment_method)
            
            # Update Booking Status to indicate user has taken action
            booking.status = BookingStatus.AWAITING_VERIFICATION
            
            self.db.commit()
            self.db.refresh(payment)
            return payment

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording payment proof: {e}")
            raise FinanceServiceError(f"Failed to record payment proof: {str(e)}")
