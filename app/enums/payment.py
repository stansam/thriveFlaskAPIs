from enum import Enum

class PaymentStatus(str, Enum):
    PENDING            = "pending"
    CONFIRMED          = "confirmed"
    FAILED             = "failed"
    REFUNDED           = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    ZELLE         = "zelle"
    CASHAPP       = "cashapp"
    PAYPAL        = "paypal"
    MPESA         = "mpesa"
    CASH          = "cash"
    CHECK         = "check"
    WIRE          = "wire"
    CRYPTO        = "crypto"