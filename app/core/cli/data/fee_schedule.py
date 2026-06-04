from datetime import date, datetime, timezone

FEE_SCHEDULES = [
    {
        "id": f"00000000-0000-0000-0006-{i:012d}",
        "name": f"Standard Fee Schedule V{i}",
        "description": f"Standard agency booking fees schedule version {i}.",
        "effective_from": date(2026, 1, 1),
        "effective_to": date(2027, 1, 1) if i < 15 else None,
        "is_active": (i == 15),  # only the latest is active
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
