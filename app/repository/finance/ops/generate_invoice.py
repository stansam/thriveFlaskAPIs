from app.models import Invoice, Booking
from app.models.enums import InvoiceStatus
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.finance.exceptions import DatabaseError, InvoiceGenerationFailed
import uuid
from datetime import datetime, timedelta, timezone

class GenerateInvoice:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, booking_id: str, total_amount: float = None) -> Invoice:
        try:
            booking = self.db.query(Booking).filter_by(id=booking_id).first()
            if not booking:
                 raise ValueError("Booking not found") 

            # TODO: Check on total amount handling.
            if total_amount is None:
                total_amount = 0.0

            new_invoice = Invoice(
                booking_id=booking_id,
                user_id=booking.user_id,
                invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}", # TODO: Implement invoice number generation util
                issued_date=datetime.now(timezone.utc),
                due_date=datetime.now(timezone.utc) + timedelta(days=7),
                total_amount=total_amount,
                currency=booking.currency,
                status=InvoiceStatus.ISSUED
            )
            
            self.db.add(new_invoice)
            self.db.commit()
            self.db.refresh(new_invoice)
            return new_invoice

        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while generating invoice: {str(e)}") from e
