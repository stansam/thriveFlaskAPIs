from typing import Optional, List
from app.extensions import db
from app.models.payment import Payment
from app.models.enums import PaymentStatus
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.payment.utils import parse_gateway_status

class PaymentRepository(BaseRepository[Payment]):
    """
    PaymentRepository coordinating the lifecycle of financial checkouts.
    Ensures absolute transaction history retention tracking attempts against external Gateways.
    """

    def __init__(self):
        super().__init__(Payment)

    @handle_db_exceptions
    def log_payment_attempt(self, invoice_id: str, gateway: str, amount: float) -> Payment:
        """Immediately persists a PENDING lock prior to transmitting an HTTP request to the Gateway."""
        data = {
            'invoice_id': invoice_id,
            'gateway': gateway,
            'amount': amount,
            'status': PaymentStatus.PENDING
        }
        return super().create(data, commit=True)

    @handle_db_exceptions
    def update_payment_transaction(self, payment_id: str, transaction_id: str, status_payload: str) -> Optional[Payment]:
        """Resolves an open payment attempt explicitly using parsed gateway response data."""
        payment = self.get_by_id(payment_id)
        if not payment:
            return None
            
        validated_status = parse_gateway_status(status_payload)
        
        payment.transaction_id = transaction_id
        payment.status = validated_status
        db.session.commit()
        
        return payment

    @handle_db_exceptions
    def get_payments_by_invoice(self, invoice_id: str) -> List[Payment]:
        """Retrieves every single transaction attempt bound to an invoice (successful or failed)."""
        return self.model.query.filter_by(invoice_id=invoice_id)\
            .order_by(self.model.created_at.desc())\
            .all()
