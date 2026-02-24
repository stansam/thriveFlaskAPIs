from app.models import Payment
from app.models.enums import PaymentStatus
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.finance.exceptions import DatabaseError, PaymentFailed, InvalidAmount
import uuid
from datetime import datetime, timezone

class ProcessRefund:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, original_payment_id: str, amount: float = None) -> Payment:
        try:
            original_payment = self.db.query(Payment).filter_by(id=original_payment_id).first()
            if not original_payment:
                raise ValueError("Original payment not found")
            
            if original_payment.status != PaymentStatus.PAID:
                raise PaymentFailed("Cannot refund a payment that is not completed")

            refund_amount = amount if amount is not None else original_payment.amount
            
            if refund_amount <= 0:
                 raise InvalidAmount("Refund amount must be positive")
            
            if refund_amount > original_payment.amount:
                 raise InvalidAmount("Cannot refund more than original payment amount")

            # TODO: Check on robust refund record creation workflow
            
            refund_payment = Payment(
                booking_id=original_payment.booking_id,
                user_id=original_payment.user_id,
                amount=refund_amount,
                currency=original_payment.currency,
                payment_method=original_payment.payment_method,
                transaction_id=f"REF-{uuid.uuid4().hex[:8].upper()}", # TODO: Implement and hook transaction ID generator util
                status=PaymentStatus.REFUNDED,
                payment_date=datetime.now(timezone.utc)
            )
            
            self.db.add(refund_payment)
            
            # TODO: Check on updating original payment status to PARTIALLY_REFUNDED or REFUNDED if full
            
            self.db.commit()
            self.db.refresh(refund_payment)
            return refund_payment

        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while processing refund: {str(e)}") from e
