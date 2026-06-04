from datetime import datetime, timezone
from decimal import Decimal
from app.enums import PackageStatus

TRAVEL_PACKAGES = [
    {
        "id": f"00000000-0000-0000-0008-{i:012d}",
        "title": f"Luxury Tour Package {i}",
        "slug": f"luxury-tour-package-{i}",
        "tagline": f"Tagline for luxury tour package {i}",
        "description": f"Detailed markdown description of the amazing package {i}.",
        "status": PackageStatus.ACTIVE if i % 2 == 0 else PackageStatus.DRAFT,
        "destination_country": "Kenya" if i % 2 == 0 else "Tanzania",
        "destination_city": "Nairobi" if i % 2 == 0 else "Dar es Salaam",
        "region": "East Africa",
        "duration_days": i + 2,
        "duration_nights": i + 1,
        "base_price_usd": Decimal(f"{200.00 * i:.2f}"),
        "price_per": "person",
        "min_participants": 2,
        "max_participants": 20,
        "flights_includable": True,
        "insurance_includable": True,
        "is_featured": (i % 5 == 0),
        "cover_image_url": f"http://localhost:5000/static/uploads/cover_{i}.jpg",
        "gallery_urls": '["http://localhost:5000/static/uploads/gallery_1.jpg", "http://localhost:5000/static/uploads/gallery_2.jpg"]',
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
