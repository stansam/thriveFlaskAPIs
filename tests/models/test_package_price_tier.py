import pytest
from decimal import Decimal
from app.models.package_price_tier import PackagePriceTier
from app.models.package import TravelPackage
from app.enums import PackageStatus

def test_package_price_tier_creation(db_session):
    """Test PackagePriceTier model creation."""
    package = TravelPackage(
        title="Price Test",
        slug="price-test",
        destination_country="Test",
        duration_days=1,
        duration_nights=0,
        base_price_usd=Decimal("100.00"),
        status=PackageStatus.ACTIVE
    )
    db_session.add(package)
    db_session.flush()

    tier = PackagePriceTier(
        package_id=package.id,
        label="Solo",
        price_usd=Decimal("150.00"),
        min_participants=1,
        max_participants=1
    )
    db_session.add(tier)
    db_session.flush()

    assert tier.id is not None
    assert tier.package.title == "Price Test"
    assert tier.price_usd == Decimal("150.00")
    assert tier.is_active is True
