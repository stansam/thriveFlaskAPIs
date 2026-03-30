import pytest
from app.repository.package_items import (
    PackageHighlightRepository, PackageInclusionRepository, PackageItineraryDayRepository
)
from app.models import PackageHighlight, PackageInclusion, PackageItineraryDay
from app.enums import InclusionType

@pytest.fixture
def highlight_repo():
    return PackageHighlightRepository()

@pytest.fixture
def inclusion_repo():
    return PackageInclusionRepository()

@pytest.fixture
def itinerary_repo():
    return PackageItineraryDayRepository()

@pytest.mark.integration
class TestPackageItemsRepository:
    def test_highlight_reorder(self, highlight_repo, db_session):
        h1 = PackageHighlight(package_id="P1", text="A", display_order=2)
        h2 = PackageHighlight(package_id="P1", text="B", display_order=1)
        db_session.add_all([h1, h2])
        db_session.flush()

        ordered_ids = [str(h2.id), str(h1.id)]
        highlight_repo.reorder("P1", ordered_ids)
        db_session.flush()

        db_session.refresh(h1)
        db_session.refresh(h2)

        assert h2.display_order == 0
        assert h1.display_order == 1

        items = highlight_repo.find_by_package("P1")
        assert len(items) == 2
        assert items[0] == h2

    def test_inclusion_queries(self, inclusion_repo, db_session):
        i1 = PackageInclusion(package_id="P1", inclusion_type=InclusionType.INCLUDED, label="L1")
        i2 = PackageInclusion(package_id="P1", inclusion_type=InclusionType.EXCLUDED, label="L2")
        db_session.add_all([i1, i2])
        db_session.flush()

        items = inclusion_repo.find_by_package("P1")
        assert len(items) == 2

    def test_itinerary_day_queries(self, itinerary_repo, db_session):
        d1 = PackageItineraryDay(package_id="P1", day_number=2, title="T2")
        d2 = PackageItineraryDay(package_id="P1", day_number=1, title="T1")
        db_session.add_all([d1, d2])
        db_session.flush()

        days = itinerary_repo.find_by_package_ordered("P1")
        assert len(days) == 2
        assert days[0] == d2  # day 1

        found = itinerary_repo.find_day("P1", 2)
        assert found == d1
        
        mx = itinerary_repo.max_day_number("P1")
        assert mx == 2
