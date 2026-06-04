from datetime import datetime, timezone
from decimal import Decimal

PACKAGE_INSURANCES = [
    {
        "id": f"00000000-0000-0000-000d-{i:012d}",
        "package_id": f"00000000-0000-0000-0008-{i:012d}",
        "provider_name": f"AIG Insurance Corp {i}",
        "policy_name": "Premium Travel Protection",
        "coverage_details": f"Covers medical emergencies, trip delays, and baggage loss up to $50,000.",
        "premium_usd": Decimal(f"{10.00 * i:.2f}"),
        "per_person_rate": Decimal("25.00"),
        "is_active": True,
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
