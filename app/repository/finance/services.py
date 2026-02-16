from sqlalchemy.orm import Session
from app.models import Payment, Invoice
from app.repository.finance.ops import (
    ProcessPayment,
    GenerateInvoice,
    CalculateFees,
    ProcessRefund
)

class FinanceService:
    def __init__(self, db: Session):
        self.db = db
    
    def process_payment(self, booking_id: str, amount: float, payment_method: str, transaction_id: str = None) -> Payment:
        return ProcessPayment(self.db).execute(booking_id, amount, payment_method, transaction_id)

    def generate_invoice(self, booking_id: str, total_amount: float = None) -> Invoice:
        return GenerateInvoice(self.db).execute(booking_id, total_amount)

    def calculate_fees(self, booking_type: str, amount: float) -> list[dict]:
        return CalculateFees(self.db).execute(booking_type, amount)

    def process_refund(self, original_payment_id: str, amount: float = None) -> Payment:
        return ProcessRefund(self.db).execute(original_payment_id, amount)
