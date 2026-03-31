# tests/interface/package/test_itinerary.py
import pytest
from unittest.mock import MagicMock, patch

from app.core.errors.handlers import BadRequestError
from app.dto import PackageItineraryDayCreateRequest, PackageItineraryDayUpdateRequest
from app.core.events.dataclass.package import (
    PackageItineraryDayAddedEvent, PackageItineraryDayUpdatedEvent, PackageItineraryDayDeletedEvent
)


@patch("app.interface.package.services.event_bus")
def test_add_itinerary_day_success(mock_bus, service, package_repo, package_itinerary_day_repo, uow, mock_package, mock_itinerary_day):
    package_repo.get_or_404.return_value = mock_package
    package_itinerary_day_repo.max_day_number.return_value = 1
    package_itinerary_day_repo.create.return_value = mock_itinerary_day

    req = PackageItineraryDayCreateRequest.model_validate({
        "day_number": 2,
        "title": "Safari Day 2",
        "description": "More lions."
    })

    result = service.add_itinerary_day("pkg-123", req, actor_id="admin-1")

    package_itinerary_day_repo.create.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageItineraryDayAddedEvent)


def test_add_itinerary_day_sequence_error(service, package_repo, package_itinerary_day_repo, mock_package):
    package_repo.get_or_404.return_value = mock_package
    package_itinerary_day_repo.max_day_number.return_value = 1

    req = PackageItineraryDayCreateRequest.model_validate({
        "day_number": 3, # Expected 2
        "title": "Skipped Day?",
        "description": "Broke the rules."
    })

    with pytest.raises(BadRequestError):
        service.add_itinerary_day("pkg-123", req, actor_id="admin-1")


@patch("app.interface.package.services.event_bus")
def test_update_itinerary_day(mock_bus, service, package_itinerary_day_repo, uow, mock_itinerary_day):
    package_itinerary_day_repo.get_or_404.return_value = mock_itinerary_day

    req = PackageItineraryDayUpdateRequest.model_validate({"title": "Updated Title"})
    result = service.update_itinerary_day("day-2", req, actor_id="admin-1")

    package_itinerary_day_repo.update.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageItineraryDayUpdatedEvent)


@patch("app.interface.package.services.event_bus")
def test_delete_itinerary_day(mock_bus, service, package_itinerary_day_repo, uow, mock_itinerary_day):
    package_itinerary_day_repo.get_or_404.return_value = mock_itinerary_day

    service.delete_itinerary_day("day-2", actor_id="admin-1")

    package_itinerary_day_repo.delete.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageItineraryDayDeletedEvent)
