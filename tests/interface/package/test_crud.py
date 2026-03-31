# tests/interface/package/test_crud.py
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.enums import PackageStatus, BookingStatus
from app.core.errors.handlers import DuplicateSlugError, BadRequestError, BusinessRuleViolationError
from app.dto import TravelPackageCreateRequest, TravelPackageUpdateRequest
from app.core.events.dataclass.package import (
    PackageCreatedEvent, PackageUpdatedEvent, PackagePublishedEvent,
    PackagePausedEvent, PackageArchivedEvent, PackageDuplicatedEvent
)

@patch("app.interface.package.services.event_bus")
def test_create_package_success(mock_bus, service, package_repo, audit_service, uow, mock_package):
    package_repo.slug_exists.return_value = False
    package_repo.create.return_value = mock_package
    package_repo.get.return_value = mock_package

    req = TravelPackageCreateRequest.model_validate({
        "title": "New Safari",
        "tagline": "A cool safari",
        "description": "Long desc",
        "status": "draft",
        "destination_country": "KE",
        "destination_city": "Nairobi",
        "region": "East Africa",
        "duration_days": 5,
        "duration_nights": 4,
        "base_price_usd": "1000.00",
        "price_per": "person",
        "min_participants": 2,
        "max_participants": 10,
        "flights_includable": True,
        "insurance_includable": True,
        "is_featured": False,
        "highlights": [],
        "inclusions": [],
        "itinerary": [],
        "price_tiers": []
    })

    result = service.create_package(req, actor_id="admin-1")

    package_repo.create.assert_called_once()
    assert uow.committed == 1
    audit_service.log.assert_called_once()
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageCreatedEvent)


@patch("app.interface.package.services.event_bus")
def test_update_package_success_slug_generation(mock_bus, service, package_repo, audit_service, uow, mock_package):
    package_repo.get.return_value = mock_package
    package_repo.slug_exists.side_effect = [True, False] # Exists first time, UUID appended passes

    req = TravelPackageUpdateRequest.model_validate({"title": "Updated Title"})
    result = service.update_package("pkg-123", req, actor_id="admin-1")

    package_repo.update.assert_called_once()
    assert uow.committed == 1
    audit_service.log.assert_called_once()
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageUpdatedEvent)


def test_update_package_duplicate_slug_raises(service, package_repo, mock_package):
    package_repo.get.return_value = mock_package
    package_repo.slug_exists.return_value = True

    req = TravelPackageUpdateRequest.model_validate({"slug": "existing-slug"})
    with pytest.raises(DuplicateSlugError):
        service.update_package("pkg-123", req, actor_id="admin-1")


@patch("app.interface.package.services.event_bus")
def test_publish_package_success(mock_bus, service, package_repo, package_price_tier_repo, package_media_repo, uow, mock_package, mock_cover_media, mock_highlight):
    mock_package.highlights = [mock_highlight]
    package_price_tier_repo.find_by_package.return_value = [MagicMock()]
    package_media_repo.find_cover.return_value = mock_cover_media
    package_repo.get.return_value = mock_package

    result = service.publish_package("pkg-123", actor_id="admin-1")

    package_repo.update.assert_called_once_with(mock_package, actor_id="admin-1", status=PackageStatus.ACTIVE)
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackagePublishedEvent)


def test_publish_package_validation_fails(service, package_repo, package_price_tier_repo, package_media_repo, mock_package):
    mock_package.highlights = [] # Missing highlight
    package_repo.get.return_value = mock_package

    with pytest.raises(BadRequestError):
        service.publish_package("pkg-123", actor_id="admin-1")


@patch("app.interface.package.services.event_bus")
def test_archive_package_success(mock_bus, service, package_repo, package_booking_repo, uow, mock_package):
    package_repo.get.return_value = mock_package
    package_booking_repo.find_by_package.return_value = []

    service.archive_package("pkg-123", actor_id="admin-1")

    package_repo.update.assert_called_once_with(mock_package, actor_id="admin-1", status=PackageStatus.ARCHIVED)
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageArchivedEvent)


def test_archive_package_fails_with_bookings(service, package_repo, package_booking_repo, mock_package):
    package_repo.get.return_value = mock_package
    package_booking_repo.find_by_package.return_value = [MagicMock()] # Active booking exists

    with pytest.raises(BusinessRuleViolationError):
        service.archive_package("pkg-123", actor_id="admin-1")


@patch("app.interface.package.services.event_bus")
def test_duplicate_package(mock_bus, service, package_repo, uow, mock_package):
    package_repo.get.return_value = mock_package
    package_repo.slug_exists.return_value = False
    
    mock_clone = mock_package
    mock_clone.id = "clone-123"
    mock_clone.media = []
    
    # Needs to return clone via get post-commit
    package_repo.get.side_effect = [mock_package, mock_clone]
    package_repo.create.return_value = mock_clone

    service.duplicate_package("pkg-123", actor_id="admin-1")

    package_repo.create.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageDuplicatedEvent)
