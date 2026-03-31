# tests/interface/package/test_highlights.py
import pytest
from unittest.mock import MagicMock, patch

from app.dto import PackageHighlightCreateRequest
from app.core.events.dataclass.package import (
    PackageHighlightAddedEvent, PackageHighlightUpdatedEvent, PackageHighlightDeletedEvent
)


@patch("app.interface.package.services.event_bus")
def test_add_highlight(mock_bus, service, package_repo, package_highlight_repo, uow, mock_package, mock_highlight):
    package_repo.get_or_404.return_value = mock_package
    package_highlight_repo.count.return_value = 0
    package_highlight_repo.create.return_value = mock_highlight

    req = PackageHighlightCreateRequest.model_validate({"text": "Great View", "icon": "camera"})
    result = service.add_highlight("pkg-123", req, actor_id="admin-1")

    package_highlight_repo.create.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageHighlightAddedEvent)


@patch("app.interface.package.services.event_bus")
def test_update_highlight(mock_bus, service, package_highlight_repo, uow, mock_highlight):
    package_highlight_repo.get_or_404.return_value = mock_highlight

    result = service.update_highlight("hl-123", {"text": "Updated View"}, actor_id="admin-1")

    package_highlight_repo.update.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageHighlightUpdatedEvent)


@patch("app.interface.package.services.event_bus")
def test_delete_highlight(mock_bus, service, package_highlight_repo, uow, mock_highlight):
    package_highlight_repo.get_or_404.return_value = mock_highlight

    service.delete_highlight("hl-123", actor_id="admin-1")

    package_highlight_repo.delete.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], PackageHighlightDeletedEvent)


def test_reorder_highlights(service, package_highlight_repo, uow):
    service.reorder_highlights("pkg-123", ["hl-2", "hl-1"], actor_id="admin-1")

    package_highlight_repo.reorder.assert_called_once_with("pkg-123", ["hl-2", "hl-1"], actor_id="admin-1")
    assert uow.committed == 1
