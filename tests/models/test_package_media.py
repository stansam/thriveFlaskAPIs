import pytest
from app.models.package_media import PackageMedia
from app.models.package import TravelPackage
from app.models.media import MediaAsset
from app.enums import AssetType, StorageBackend, PackageStatus

def test_package_media_creation(db_session):
    """Test PackageMedia junction model."""
    package = TravelPackage(
        title="Media Test",
        slug="media-test",
        destination_country="Test",
        duration_days=1,
        duration_nights=0,
        base_price_usd=100,
        status=PackageStatus.ACTIVE
    )
    db_session.add(package)
    db_session.flush()

    asset = MediaAsset(
        original_filename="test.jpg",
        storage_key="pkg/test.jpg",
        storage_backend=StorageBackend.LOCAL,
        cdn_url="http://localhost/test.jpg",
        asset_type=AssetType.IMAGE_JPEG
    )
    db_session.add(asset)
    db_session.flush()

    pkg_media = PackageMedia(
        package_id=package.id,
        asset_id=asset.id,
        is_cover=True
    )
    db_session.add(pkg_media)
    db_session.commit()

    assert pkg_media.id is not None
    assert pkg_media.package.title == "Media Test"
    assert pkg_media.asset.original_filename == "test.jpg"
    assert pkg_media.is_cover is True
