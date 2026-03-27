import pytest
from decimal import Decimal
from app.models.package import TravelPackage
from app.enums import PackageStatus

def test_travel_package_creation(db_session):
    """Test TravelPackage model creation and defaults."""
    package = TravelPackage(
        title="Dubai Luxury Escape",
        slug="dubai-luxury-escape",
        destination_country="UAE",
        destination_city="Dubai",
        duration_days=5,
        duration_nights=4,
        base_price_usd=Decimal("1899.00"),
        status=PackageStatus.ACTIVE
    )
    db_session.add(package)
    db_session.commit()

    assert package.id is not None
    assert package.slug == "dubai-luxury-escape"
    assert package.is_featured is False
    assert package.flights_includable is False
