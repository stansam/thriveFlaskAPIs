from app.repository.invoice.repository import InvoiceRepository
from app.repository.payment.repository import PaymentRepository

print("Imports successful!")
repo1 = InvoiceRepository()
repo2 = PaymentRepository()
print("Instantiations successful!")
