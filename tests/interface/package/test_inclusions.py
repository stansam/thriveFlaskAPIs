# tests/interface/package/test_inclusions.py
import pytest
from unittest.mock import MagicMock, patch

from app.dto import PackageInclusionCreateRequest
from app.core.events.dataclass.package import (
    PackageInclusionAddedEvent, PackageInclusionUpdatedEvent, PackageInclusionDeletedEvent
)


@patch("app.interface.package.services.event_bus")
def test_add_inclusion(mock_bus, service, package_repo, package_inclusion_repo, uow, mock_package, mock_inclusion):
    package_repo.get.return_value = mock_package
    package_inclusion_repo.create.return_value = mock_inclusion

    req = PackageInclusionCreateRequest.model_validate({
        "inclusion_type": "included",
        "label": "Free Drinks",
        "display_order": 1
    })

    result = service.add_inclusion("pkg-123", req, actor_id="admin-1")

    package_inclusion_repo.create.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageInclusionAddedEvent)


@patch("app.interface.package.services.event_bus")
def test_update_inclusion(mock_bus, service, package_inclusion_repo, uow, mock_inclusion):
    package_inclusion_repo.get.return_value = mock_inclusion

    result = service.update_inclusion("inc-1", {"label": "Updated Drinks"}, actor_id="admin-1")

    package_inclusion_repo.update.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageInclusionUpdatedEvent)


@patch("app.interface.package.services.event_bus")
def test_delete_inclusion(mock_bus, service, package_inclusion_repo, uow, mock_inclusion):
    package_inclusion_repo.get.return_value = mock_inclusion

    service.delete_inclusion("inc-1", actor_id="admin-1")

    package_inclusion_repo.delete.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageInclusionDeletedEvent)
