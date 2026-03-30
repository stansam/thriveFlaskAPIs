import pytest
from app.repository.package_media import PackageMediaRepository
from app.models import PackageMedia

@pytest.fixture
def repo():
    return PackageMediaRepository()

@pytest.mark.integration
class TestPackageMediaRepository:
    def test_set_and_find_cover(self, repo, db_session):
        # We don't need real MediaAsset IDs for SQLite tests enforcing NO FKs
        m1 = PackageMedia(package_id="P1", asset_id="A1", is_cover=False, display_order=1)
        db_session.add(m1)
        db_session.flush()

        # promote A1 to cover
        new_cover = repo.set_cover("P1", "A1")
        db_session.flush()
        db_session.refresh(m1)

        assert m1.is_cover is True
        assert new_cover.id == m1.id
        assert repo.find_cover("P1") == m1

        # set A2 as cover (creates new if not exists)
        cover2 = repo.set_cover("P1", "A2")
        db_session.flush()
        db_session.refresh(m1)

        assert m1.is_cover is False
        assert cover2.is_cover is True
        assert cover2.asset_id == "A2"
        assert repo.find_cover("P1") == cover2

    def test_find_galleries(self, repo, db_session):
        m1 = PackageMedia(package_id="P1", asset_id="A1", is_cover=False, display_order=1)
        m2 = PackageMedia(package_id="P1", asset_id="A2", is_cover=True, display_order=0)
        m3 = PackageMedia(package_id="P1", asset_id="A3", is_cover=False, display_order=2, itinerary_day_id="DAY1")
        db_session.add_all([m1, m2, m3])
        db_session.flush()

        gallery = repo.find_gallery("P1")
        assert len(gallery) == 1
        assert gallery[0] == m1  # m2 is cover, m3 is day media

        day_media = repo.find_day_media("DAY1")
        assert len(day_media) == 1
        assert day_media[0] == m3
