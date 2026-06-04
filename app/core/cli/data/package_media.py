from datetime import datetime, timezone

PACKAGE_MEDIA_ITEMS = [
    {
        "id": f"00000000-0000-0000-000f-{i:012d}",
        "package_id": f"00000000-0000-0000-0008-{i:012d}",
        "asset_id": f"00000000-0000-0000-000e-{i:012d}",
        "itinerary_day_id": f"00000000-0000-0000-000b-{i:012d}" if i <= 10 else None,
        "is_cover": True,
        "display_order": 0,
        "caption": f"Cover Image for Package {i}",
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
