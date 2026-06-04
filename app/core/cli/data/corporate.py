from datetime import datetime, timezone
from decimal import Decimal
from app.enums import SubscriptionTier

CORPORATE_ACCOUNTS = [
    {
        "id": f"00000000-0000-0000-0002-{i:012d}",
        "company_name": f"Enterprise Corp {i}",
        "industry": "Technology" if i % 3 == 0 else ("Finance" if i % 3 == 1 else "Healthcare"),
        "billing_email": f"billing@enterprise{i}.com",
        "billing_address": f"{100 * i} Business Rd, Suite {i}, New York, NY 10001",
        "tax_id": f"US-{1234567 + i:07d}",
        "primary_contact_name": f"Contact Person {i}",
        "primary_contact_phone": f"+1555020{i:02d}",
        "is_active": True,
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]

CORPORATE_SUBSCRIPTIONS = [
    {
        "id": f"00000000-0000-0000-0003-{i:012d}",
        "account_id": f"00000000-0000-0000-0002-{i:012d}",
        "tier": SubscriptionTier.GOLD if i % 3 == 0 else (SubscriptionTier.SILVER if i % 3 == 1 else SubscriptionTier.BRONZE),
        "monthly_fee": Decimal("1000.00") if i % 3 == 0 else (Decimal("500.00") if i % 3 == 1 else Decimal("200.00")),
        "bookings_limit": None if i % 3 == 0 else (100 if i % 3 == 1 else 30),
        "bookings_used": i * 2,
        "concierge_247": i % 3 == 0,
        "billing_cycle_start": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "billing_cycle_end": datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc),
        "is_active": True,
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
