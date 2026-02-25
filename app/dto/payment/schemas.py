from dataclasses import dataclass
from typing import Optional
from app.models.enums import PaymentMethod, PaymentStatus

@dataclass
class GenerateInvoiceDTO:
    user_id: str
    amount: float
    currency: str = "USD"
    booking_id: Optional[str] = None
    subscription_id: Optional[str] = None

@dataclass
class SubmitPaymentProofDTO:
    booking_id: str
    payment_method: PaymentMethod
    payment_proof_url: str
    transaction_id: Optional[str] = None

@dataclass
class VerifyPaymentDTO:
    payment_id: str
    status: PaymentStatus
    admin_notes: Optional[str] = None
