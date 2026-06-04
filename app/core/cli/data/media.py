from datetime import datetime, timezone
from app.enums import AssetType, AssetOwnerType, StorageBackend

MEDIA_ASSETS = [
    {
        "id": f"00000000-0000-0000-000e-{i:012d}",
        "original_filename": f"asset_file_{i}.jpg" if i <= 10 else f"receipt_{i}.pdf",
        "storage_key": f"uploads/asset_file_{i}.jpg" if i <= 10 else f"receipts/receipt_{i}.pdf",
        "storage_backend": StorageBackend.LOCAL,
        "cdn_url": f"http://localhost:5000/static/uploads/asset_file_{i}.jpg" if i <= 10 else f"http://localhost:5000/static/receipts/receipt_{i}.pdf",
        "asset_type": AssetType.IMAGE_JPEG if i <= 10 else AssetType.DOCUMENT_PDF,
        "file_size_bytes": 1024 * i * 50,
        "width_px": 800 if i <= 10 else None,
        "height_px": 600 if i <= 10 else None,
        "alt_text": f"Alt text description for asset {i}" if i <= 10 else None,
        "is_public": i <= 10,
        "checksum_sha256": f"a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6{i:02d}",
        "owner_type": AssetOwnerType.TRAVEL_PACKAGE if i <= 5 else (AssetOwnerType.PACKAGE_ITINERARY_DAY if i <= 10 else AssetOwnerType.PAYMENT),
        "owner_id": f"00000000-0000-0000-0008-{i:012d}" if i <= 5 else (f"00000000-0000-0000-000b-{i:012d}" if i <= 10 else f"00000000-0000-0000-0014-{(i-10):012d}"),
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
