import pytest
from app.models.package_items import PackageHighlight, PackageInclusion, PackageItineraryDay
from app.models.package import TravelPackage
from app.enums import InclusionType, PackageStatus
from decimal import Decimal

def test_package_items_creation(db_session):
    """Test Package items (Highlight, Inclusion, ItineraryDay)."""
    package = TravelPackage(
        title="Items Test",
        slug="items-test",
        destination_country="Test",
        duration_days=1,
        duration_nights=0,
        base_price_usd=Decimal("100.00"),
        status=PackageStatus.ACTIVE
    )
    db_session.add(package)
    db_session.flush()

    highlight = PackageHighlight(package_id=package.id, text="Great view")
    inclusion = PackageInclusion(package_id=package.id, inclusion_type=InclusionType.INCLUDED, label="Breakfast")
    itinerary = PackageItineraryDay(package_id=package.id, day_number=1, title="Day 1")
    
    db_session.add_all([highlight, inclusion, itinerary])
    db_session.flush()

    assert highlight.id is not None
    assert inclusion.id is not None
    assert itinerary.id is not None
    assert len(package.highlights) == 1
    assert len(package.inclusions) == 1
    assert len(package.itinerary_days) == 1
