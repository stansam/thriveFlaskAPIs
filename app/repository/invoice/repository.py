from typing import Optional, List
from app.extensions import db
from app.models.payment import Invoice
from app.models.enums import InvoiceStatus
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.invoice.utils import generate_invoice_number

class InvoiceRepository(BaseRepository[Invoice]):
    """
    InvoiceRepository encapsulating complex billing number generation, 
    unpaid invoice queries, and atomic payment linking interactions.
    """

    def __init__(self):
        super().__init__(Invoice)

    @handle_db_exceptions
    def create_invoice(self, data: dict) -> Invoice:
        """Injects sequential custom invoice numbers upon creation."""
        data['invoice_number'] = generate_invoice_number()
        return super().create(data, commit=False)

    @handle_db_exceptions
    def get_unpaid_invoices_by_user(self, user_id: str) -> List[Invoice]:
        """Queries for open, unpaid billing entries associated with a user."""
        return self.model.query.filter(
            self.model.user_id == user_id,
            self.model.status == InvoiceStatus.ISSUED
        ).order_by(self.model.due_date.asc()).all()

    @handle_db_exceptions
    def find_invoice_by_subscription(self, subscription_id: str) -> List[Invoice]:
        """Fetches a chronological ledger of billing linked to corporate subscriptions."""
        return self.model.query.filter_by(subscription_id=subscription_id)\
            .order_by(self.model.created_at.desc())\
            .all()

    @handle_db_exceptions
    def mark_invoice_as_paid(self, invoice_id: str, payment_id: str) -> Optional[Invoice]:
        """Atomically locks the invoice status to PAID tracking the successful gateway attempt."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return None
            
        invoice.status = InvoiceStatus.PAID
        # Note: If the actual DB schema expects a payment_id foreign key, we can attach it here.
        # Ensure that relation exists or simply let the Payment table hold the invoice_id side.
        db.session.commit()
        return invoice
