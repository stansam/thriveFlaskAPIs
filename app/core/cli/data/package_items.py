from datetime import datetime, timezone
from decimal import Decimal
from app.enums import InclusionType

PACKAGE_HIGHLIGHTS = [
    {
        "id": f"00000000-0000-0000-0009-{i:012d}",
        "package_id": f"00000000-0000-0000-0008-{i:012d}",
        "text": f"Spectacular Highlight for Package {i}",
        "icon": "🌟",
        "display_order": 1,
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]

PACKAGE_INCLUSIONS = [
    {
        "id": f"00000000-0000-0000-000a-{i:012d}",
        "package_id": f"00000000-0000-0000-0008-{i:012d}",
        "inclusion_type": InclusionType.INCLUDED if i % 2 == 0 else InclusionType.OPTIONAL,
        "label": f"Inclusion description {i}",
        "notes": "Available upon request" if i % 2 != 0 else "Fully covered",
        "extra_cost_usd": Decimal("150.00") if i % 2 != 0 else None,
        "display_order": 1,
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]

PACKAGE_ITINERARY_DAYS = [
    {
        "id": f"00000000-0000-0000-000b-{i:012d}",
        "package_id": f"00000000-0000-0000-0008-{i:012d}",
        "day_number": 1,
        "title": f"Day 1: Arrival & Welcome for Package {i}",
        "description": f"Welcome to the tour of package {i}! Check-in and relax.",
        "activities": "Transfer from airport to hotel\nWelcome dinner",
        "meals_included": "Dinner",
        "accommodation": f"Grand Palace Hotel {i}",
        "image_url": f"http://localhost:5000/static/uploads/day1_pkg_{i}.jpg",
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
