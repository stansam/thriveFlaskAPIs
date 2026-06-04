from datetime import datetime, timezone
from decimal import Decimal
from app.enums import LoyaltyTransactionType

LOYALTY_ENTRIES = [
    {
        "id": f"00000000-0000-0000-0016-{i:012d}",
        "client_id": f"00000000-0000-0000-0004-{i:012d}",
        "transaction_type": LoyaltyTransactionType.REFERRAL_CREDIT if i % 2 == 0 else LoyaltyTransactionType.MANUAL_CREDIT,
        "amount_usd": Decimal("10.00") if i % 2 == 0 else Decimal("25.00"),
        "description": "Earned referral reward." if i % 2 == 0 else "Welcome bonus credit.",
        "booking_id": None,
        "referral_id": f"00000000-0000-0000-0015-{i:012d}" if i % 2 == 0 else None,
        "expires_at": datetime(2027, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
