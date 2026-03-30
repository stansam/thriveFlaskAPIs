import pytest
from decimal import Decimal
from werkzeug.exceptions import NotFound

from app.repository.package import TravelPackageRepository
from app.models import TravelPackage
from app.enums import PackageStatus

@pytest.fixture
def repo():
    return TravelPackageRepository()

def build_package(slug: str, title: str, status: PackageStatus, is_featured: bool = False, base_price=100.0) -> TravelPackage:
    return TravelPackage(
        title=title, slug=slug, status=status,
        destination_country="France", duration_days=5, duration_nights=4,
        base_price_usd=Decimal(str(base_price)), price_per="person",
        min_participants=1, flights_includable=False, insurance_includable=False,
        is_featured=is_featured
    )

@pytest.mark.integration
class TestTravelPackageRepository:
    def test_find_by_slug(self, repo, db_session):
        p = build_package("test-slug", "Test Tour", PackageStatus.ACTIVE)
        db_session.add(p)
        db_session.flush()

        assert repo.find_by_slug("test-slug") == p
        assert repo.find_by_slug("unknown") is None

        assert repo.find_by_slug_or_404("test-slug") == p
        with pytest.raises(NotFound):
            repo.find_by_slug_or_404("unknown")

    def test_find_active_and_featured(self, repo, db_session):
        p1 = build_package("active-feat", "A1", PackageStatus.ACTIVE, is_featured=True)
        p2 = build_package("active-norm", "A2", PackageStatus.ACTIVE, is_featured=False)
        p3 = build_package("draft-norm", "D1", PackageStatus.DRAFT, is_featured=True)
        db_session.add_all([p1, p2, p3])
        db_session.flush()

        active = repo.find_active()
        assert p1 in active
        assert p2 in active
        assert p3 not in active

        featured = repo.find_featured()
        assert p1 in featured
        assert p2 not in featured
        assert p3 not in featured  # Drafts shouldn't be here

    def test_slug_exists(self, repo, db_session):
        p = build_package("exist-slug", "E", PackageStatus.ACTIVE)
        db_session.add(p)
        db_session.flush()

        assert repo.slug_exists("exist-slug") is True
        assert repo.slug_exists("exist-slug", exclude_id=str(p.id)) is False
        assert repo.slug_exists("new-slug") is False

    def test_paginate_packages(self, repo, db_session):
        p1 = build_package("p1", "Paris Tour", PackageStatus.ACTIVE, base_price=500)
        p2 = build_package("p2", "London Tour", PackageStatus.ACTIVE, base_price=800)
        p2.destination_country = "UK"
        db_session.add_all([p1, p2])
        db_session.flush()

        page = repo.paginate_packages(status=PackageStatus.ACTIVE, min_price=600)
        assert p2 in page.items
        assert p1 not in page.items
