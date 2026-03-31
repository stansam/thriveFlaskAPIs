# tests/interface/package/conftest.py
import pytest
from unittest.mock import MagicMock
from decimal import Decimal

from app.core.unit_of_work import IUnitOfWork
from app.interface.package import PackageService
from app.enums import PackageStatus, BookingStatus


class _FakeUoW(IUnitOfWork):
    def __init__(self) -> None:
        self.committed = 0
        self.rolled_back = 0

    def __enter__(self) -> "_FakeUoW":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[override]
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        self.committed += 1

    def rollback(self) -> None:
        self.rolled_back += 1


@pytest.fixture()
def uow() -> _FakeUoW:
    return _FakeUoW()


@pytest.fixture()
def package_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def package_highlight_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def package_inclusion_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def package_itinerary_day_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def package_price_tier_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def package_media_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def package_booking_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def audit_service() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def service(
    package_repo,
    package_highlight_repo,
    package_inclusion_repo,
    package_itinerary_day_repo,
    package_price_tier_repo,
    package_media_repo,
    package_booking_repo,
    audit_service,
    uow,
) -> PackageService:
    return PackageService(
        package_repo=package_repo,
        package_highlight_repo=package_highlight_repo,
        package_inclusion_repo=package_inclusion_repo,
        package_itinerary_day_repo=package_itinerary_day_repo,
        package_price_tier_repo=package_price_tier_repo,
        package_media_repo=package_media_repo,
        package_booking_repo=package_booking_repo,
        audit_service=audit_service,
        uow=uow,
    )


@pytest.fixture()
def mock_package() -> MagicMock:
    pkg = MagicMock()
    pkg.id = "pkg-123"
    pkg.title = "Kenya Safari"
    pkg.slug = "kenya-safari"
    pkg.tagline = "Best Safari"
    pkg.description = "A great experience."
    pkg.status = PackageStatus.DRAFT
    pkg.destination_country = "KE"
    pkg.destination_city = "Nairobi"
    pkg.region = "East Africa"
    pkg.duration_days = 5
    pkg.duration_nights = 4
    pkg.base_price_usd = Decimal("1200.00")
    pkg.price_per = "person"
    pkg.min_participants = 1
    pkg.max_participants = 10
    pkg.flights_includable = True
    pkg.insurance_includable = True
    pkg.is_featured = False
    
    # Mock nested relationships natively returning standard python lists
    pkg.highlights = []
    pkg.inclusions = []
    pkg.itinerary_days = []
    pkg.price_tiers = []
    pkg.media = []
    pkg.cover_image_url = None
    pkg.gallery = []
    pkg.total_bookings = 0
    
    from datetime import datetime, timezone
    pkg.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    pkg.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    pkg.created_by_id = None
    pkg.updated_by_id = None
    return pkg


@pytest.fixture()
def mock_cover_media() -> MagicMock:
    media = MagicMock()
    media.is_cover = True
    media.asset.cdn_url = "https://cdn.example.com/cover.jpg"
    return media

@pytest.fixture()
def mock_highlight() -> MagicMock:
    hl = MagicMock()
    hl.id = "hl-123"
    hl.package_id = "pkg-123"
    hl.text = "Great View"
    hl.icon = "camera"
    hl.display_order = 0
    from datetime import datetime, timezone
    hl.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    hl.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    hl.created_by_id = None
    hl.updated_by_id = None
    return hl

@pytest.fixture()
def mock_inclusion() -> MagicMock:
    inc = MagicMock()
    inc.id = "inc-1"
    inc.package_id = "pkg-123"
    from app.enums import InclusionType
    inc.inclusion_type = InclusionType.INCLUDED
    inc.label = "Free Drinks"
    inc.notes = None
    inc.extra_cost_usd = None
    inc.display_order = 1
    from datetime import datetime, timezone
    inc.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    inc.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    inc.created_by_id = None
    inc.updated_by_id = None
    return inc

@pytest.fixture()
def mock_itinerary_day() -> MagicMock:
    day = MagicMock()
    day.id = "day-2"
    day.package_id = "pkg-123"
    day.day_number = 2
    day.title = "Safari Day 2"
    day.description = "More lions."
    day.activities = None
    day.meals_included = None
    day.accommodation = None
    day.media = []
    from datetime import datetime, timezone
    day.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    day.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    day.created_by_id = None
    day.updated_by_id = None
    return day

@pytest.fixture()
def mock_price_tier() -> MagicMock:
    tier = MagicMock()
    tier.id = "tier-1"
    tier.package_id = "pkg-123"
    tier.label = "Standard"
    tier.price_usd = Decimal("1000.00")
    tier.price_per = "person"
    tier.min_participants = 1
    tier.max_participants = 5
    tier.is_add_on = False
    tier.is_active = True
    from datetime import datetime, timezone
    tier.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    tier.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    tier.created_by_id = None
    tier.updated_by_id = None
    return tier
