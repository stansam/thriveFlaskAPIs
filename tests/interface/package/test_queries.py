# tests/interface/package/test_queries.py
import pytest
from unittest.mock import MagicMock

from app.core.errors.handlers import NotFoundError

def test_get_package_success(service, package_repo, mock_package):
    package_repo.get_or_404.return_value = mock_package
    result = service.get_package("pkg-123")
    assert result.id == "pkg-123"
    assert result.title == "Kenya Safari"
    package_repo.get_or_404.assert_called_once_with("pkg-123")


def test_get_package_with_cover(service, package_repo, mock_package, mock_cover_media):
    mock_package.media = [mock_cover_media]
    package_repo.get_or_404.return_value = mock_package
    result = service.get_package("pkg-123")
    assert result.cover_image_url == "https://cdn.example.com/cover.jpg"


def test_get_package_not_found(service, package_repo):
    package_repo.get_or_404.side_effect = NotFoundError("Package not found")
    with pytest.raises(NotFoundError):
        service.get_package("invalid-id")


def test_get_package_by_slug_success(service, package_repo, mock_package):
    package_repo.find_by_slug_or_404.return_value = mock_package
    result = service.get_package_by_slug("kenya-safari")
    assert result.slug == "kenya-safari"
    package_repo.find_by_slug_or_404.assert_called_once_with("kenya-safari")


def test_list_packages(service, package_repo, mock_package):
    page_mock = MagicMock()
    page_mock.items = [mock_package]
    page_mock.total = 1
    page_mock.page = 1
    page_mock.per_page = 20
    page_mock.total_pages = 1
    page_mock.has_next = False
    page_mock.has_prev = False

    package_repo.paginate_packages.return_value = page_mock

    result = service.list_packages(page=1, per_page=20)
    assert len(result["items"]) == 1
    assert result["items"][0].id == "pkg-123"
    assert result["total"] == 1
    package_repo.paginate_packages.assert_called_once()
