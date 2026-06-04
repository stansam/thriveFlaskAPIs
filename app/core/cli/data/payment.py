from datetime import datetime, timezone
from decimal import Decimal
from app.enums import PaymentMethod, PaymentStatus

PAYMENTS = [
    {
        "id": f"00000000-0000-0000-0014-{i:012d}",
        "booking_id": f"00000000-0000-0000-0010-000000000{100+i:03d}",  # Flight bookings
        "amount_usd": Decimal("50.00") if i % 2 == 0 else Decimal("15.00"),
        "currency": "USD",
        "exchange_rate": None,
        "method": PaymentMethod.BANK_TRANSFER if i % 2 == 0 else PaymentMethod.PAYPAL,
        "status": PaymentStatus.CONFIRMED if i % 2 == 0 else PaymentStatus.PENDING,
        "reference": f"TXN-REF-{10000 + i}",
        "payment_proof_url": f"http://localhost:5000/static/receipts/receipt_{i}.pdf" if i > 10 else None,
        "paid_at": datetime(2026, 6, 2, 11, 0, 0, tzinfo=timezone.utc) if i % 2 == 0 else None,
        "notes": f"Payment {i} description notes.",
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
