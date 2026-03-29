import pytest
from decimal import Decimal
from datetime import date
from app.models.package_booking import PackageBooking
from app.models.package import TravelPackage
from app.models.client import Client
from app.enums import BookingStatus, BookingServiceType, ClientType, PackageStatus

def test_package_booking_creation(db_session):
    """Test PackageBooking model as a polymorphic child."""
    client = Client(
        first_name="Pkg",
        last_name="Booker",
        email="pkg.booker@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    package = TravelPackage(
        title="Test Package",
        slug="test-pkg",
        destination_country="Test",
        duration_days=3,
        duration_nights=2,
        base_price_usd=Decimal("500.00"),
        status=PackageStatus.ACTIVE
    )
    db_session.add(package)
    db_session.flush()

    booking = PackageBooking(
        reference_number="TG-PKG-123",
        service_type=BookingServiceType.PACKAGE,
        status=BookingStatus.CONFIRMED,
        client_id=client.id,
        package_id=package.id,
        total_service_fee_usd=Decimal("50.00"),
        num_participants=2,
        travel_date=date(2024, 12, 1),
        price_per_person_usd=Decimal("500.00"),
        total_package_cost_usd=Decimal("1000.00")
    )
    db_session.add(booking)
    db_session.flush()

    assert booking.id is not None
    assert booking.package.title == "Test Package"
    assert booking.service_type == BookingServiceType.PACKAGE
