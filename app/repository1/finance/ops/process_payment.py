from app.models import Payment, Booking, Invoice
from app.models.enums import PaymentStatus, InvoiceStatus, BookingStatus
from app.extensions import db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.finance.exceptions import DatabaseError, PaymentFailed, InvalidAmount
import uuid
from datetime import datetime, timezone

class ProcessPayment:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, booking_id: str, amount: float, payment_method: str, transaction_id: str = None) -> Payment:
        try:
            if amount <= 0:
                raise InvalidAmount("Payment amount must be positive")

            booking = self.db.query(Booking).filter_by(id=booking_id).first()
            if not booking:
                 raise ValueError("Booking not found") # TODO: Check on need for BookingNotFound
            
            new_payment = Payment(
                booking_id=booking_id,
                user_id=booking.user_id,
                amount=amount,
                currency=booking.currency, # TODO: Check on currency handling
                payment_method=payment_method,
                transaction_id=transaction_id or f"TXN-{uuid.uuid4().hex[:8].upper()}", # TODO: Implement tranaction ID generator util
                status=PaymentStatus.PAID,
                payment_date=datetime.now(timezone.utc)
            )
            
            self.db.add(new_payment)
            
            # TODO: Check if total paid covers total cost (Mock logic: assume this payment covers it)
            
            if booking.status == BookingStatus.PENDING:
                booking.status = BookingStatus.CONFIRMED
                
            self.db.commit()
            self.db.refresh(new_payment)
            return new_payment

        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while processing payment: {str(e)}") from e
