import pytest
from app.repository.media import MediaAssetRepository
from app.models import MediaAsset
from app.enums import AssetType, AssetOwnerType, StorageBackend

@pytest.fixture
def repo():
    return MediaAssetRepository()

@pytest.mark.integration
class TestMediaAssetRepository:
    def test_queries(self, repo, db_session):
        a1 = MediaAsset(
            original_filename="img.jpg", storage_key="keys/img.jpg",
            storage_backend=StorageBackend.S3, cdn_url="url",
            asset_type=AssetType.IMAGE_JPEG, file_size_bytes=100,
            owner_type=AssetOwnerType.TRAVEL_PACKAGE, owner_id="P1",
            checksum_sha256="hash123"
        )
        a2 = MediaAsset(
            original_filename="doc.pdf", storage_key="keys/doc.pdf",
            storage_backend=StorageBackend.S3, cdn_url="url2",
            asset_type=AssetType.DOCUMENT_PDF, file_size_bytes=200,
            owner_type=AssetOwnerType.TRAVEL_PACKAGE, owner_id="P1",
            checksum_sha256="hash456"
        )
        db_session.add_all([a1, a2])
        db_session.flush()

        by_owner = repo.find_by_owner(AssetOwnerType.TRAVEL_PACKAGE, "P1")
        assert len(by_owner) == 2

        by_owner_type = repo.find_by_owner(AssetOwnerType.TRAVEL_PACKAGE, "P1", asset_type=AssetType.IMAGE_JPEG)
        assert len(by_owner_type) == 1
        assert by_owner_type[0] == a1

        assert repo.find_by_storage_key("keys/img.jpg") == a1
        assert repo.find_by_checksum("hash456") == a2
