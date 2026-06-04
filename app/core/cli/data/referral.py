from datetime import datetime, timezone
from decimal import Decimal
from app.enums import ReferralStatus

REFERRALS = [
    {
        "id": f"00000000-0000-0000-0015-{i:012d}",
        "referrer_id": f"00000000-0000-0000-0004-{i:012d}",
        "referee_id": f"00000000-0000-0000-0004-{(i % 15 + 1):012d}",
        "status": ReferralStatus.CREDITED if i % 2 == 0 else ReferralStatus.PENDING,
        "credit_usd": Decimal("10.00"),
        "qualifying_booking_id": f"00000000-0000-0000-0010-000000000{100+i:03d}" if i % 2 == 0 else None,
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
