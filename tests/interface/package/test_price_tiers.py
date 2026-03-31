# tests/interface/package/test_price_tiers.py
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.core.errors.handlers import BadRequestError
from app.dto import PackagePriceTierCreateRequest, PackagePriceTierUpdateRequest
from app.core.events.dataclass.package import (
    PackagePriceTierAddedEvent, PackagePriceTierUpdatedEvent, PackagePriceTierDeactivatedEvent
)


@patch("app.interface.package.services.event_bus")
def test_add_price_tier_success(mock_bus, service, package_repo, package_price_tier_repo, uow, mock_package, mock_price_tier):
    package_repo.get_or_404.return_value = mock_package
    package_price_tier_repo.find_by_package.return_value = []
    package_price_tier_repo.create.return_value = mock_price_tier

    req = PackagePriceTierCreateRequest.model_validate({
        "label": "Standard",
        "price_usd": "1000.00",
        "price_per": "person",
        "min_participants": 1,
        "max_participants": 5,
        "is_add_on": False,
        "is_active": True
    })

    result = service.add_price_tier("pkg-123", req, actor_id="admin-1")

    package_price_tier_repo.create.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackagePriceTierAddedEvent)


def test_add_price_tier_overlap_raises(service, package_repo, package_price_tier_repo, mock_package):
    package_repo.get_or_404.return_value = mock_package
    
    existing = MagicMock()
    existing.is_add_on = False
    existing.min_participants = 1
    existing.max_participants = 5
    package_price_tier_repo.find_by_package.return_value = [existing]

    req = PackagePriceTierCreateRequest.model_validate({
        "label": "Overlap",
        "price_usd": "900.00",
        "price_per": "person",
        "min_participants": 4, # Overlaps [1, 5]
        "max_participants": 10,
        "is_add_on": False,
        "is_active": True
    })

    with pytest.raises(BadRequestError):
        service.add_price_tier("pkg-123", req, actor_id="admin-1")


@patch("app.interface.package.services.event_bus")
def test_update_price_tier(mock_bus, service, package_price_tier_repo, uow, mock_price_tier):
    package_price_tier_repo.get_or_404.return_value = mock_price_tier

    req = PackagePriceTierUpdateRequest.model_validate({"price_usd": "1200.00"})
    result = service.update_price_tier("tier-1", req, actor_id="admin-1")

    package_price_tier_repo.update.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackagePriceTierUpdatedEvent)


@patch("app.interface.package.services.event_bus")
def test_deactivate_price_tier(mock_bus, service, package_price_tier_repo, uow, mock_price_tier):
    package_price_tier_repo.get_or_404.return_value = mock_price_tier

    service.deactivate_price_tier("tier-1", actor_id="admin-1")

    package_price_tier_repo.update.assert_called_once_with(mock_price_tier, actor_id="admin-1", is_active=False)
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackagePriceTierDeactivatedEvent)


def test_resolve_price_for_booking_success(service, package_price_tier_repo):
    base_tier = MagicMock()
    base_tier.price_usd = Decimal("1000.00")
    
    flight_tier = MagicMock()
    flight_tier.price_usd = Decimal("300.00")

    def side_effect(pkg, parts, is_add_on=False):
        return flight_tier if is_add_on else base_tier

    package_price_tier_repo.find_matching_tier.side_effect = side_effect

    total = service.resolve_price_for_booking("pkg-123", num_participants=2, add_flight=True)
    
    assert total == Decimal("2600.00")


def test_resolve_price_missing_tier_raises(service, package_price_tier_repo):
    package_price_tier_repo.find_matching_tier.return_value = None

    with pytest.raises(BadRequestError):
        service.resolve_price_for_booking("pkg-123", num_participants=20)
