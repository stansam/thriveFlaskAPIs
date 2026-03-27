import pytest
from app.models.media import MediaAsset
from app.enums import AssetType, AssetOwnerType, StorageBackend

def test_media_asset_creation(db_session):
    """Test MediaAsset model creation and polymorphic fields."""
    asset = MediaAsset(
        original_filename="beach.jpg",
        storage_key="packages/123/beach.jpg",
        storage_backend=StorageBackend.S3,
        cdn_url="https://cdn.example.com/beach.jpg",
        asset_type=AssetType.IMAGE_JPEG,
        file_size_bytes=1024576,
        owner_type=AssetOwnerType.TRAVEL_PACKAGE,
        owner_id="package-123"
    )
    db_session.add(asset)
    db_session.commit()

    assert asset.id is not None
    assert asset.storage_backend == StorageBackend.S3
    assert asset.is_public is True  # Default
    assert asset.owner_type == AssetOwnerType.TRAVEL_PACKAGE
