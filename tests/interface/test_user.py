"""
Unit tests for UserService.

Covers CRUD operations and preference management for users.
All external dependencies (repos, UoW, event bus) are replaced with
MagicMock instances to test logic in complete isolation without a database.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call

from app.core.unit_of_work import IUnitOfWork
from app.core.errors.handlers import (
    DuplicateEmailError,
    NotFoundError,
    BadRequestError,
)
from app.dto import (
    UserCreateRequest,
    UserUpdateRequest,
    UserPreferenceUpdateRequest,
)
from app.enums import UserRole, AuditActionType
from app.interface.user import UserService
from app.core.events.dataclass.user import (
    UserCreatedEvent,
    UserUpdatedEvent,
    UserDeactivatedEvent,
    UserReactivatedEvent,
    UserPreferenceUpdatedEvent,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

class _FakeUoW(IUnitOfWork):
    """In-memory Unit of Work for testing."""

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
def user_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def user_preference_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def audit_service() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def service(user_repo, user_preference_repo, audit_service, uow) -> UserService:
    return UserService(
        user_repo=user_repo,
        user_preference_repo=user_preference_repo,
        audit_service=audit_service,
        uow=uow,
    )


@pytest.fixture()
def mock_user() -> MagicMock:
    user = MagicMock()
    user.id = "user-abc-123"
    user.email = "test@thrive.com"
    user.full_name = "Test User"
    user.phone = "0712345678"
    user.role = UserRole.AGENT
    user.is_active = True
    user.created_at = None
    user.updated_at = None
    user.created_by_id = None
    user.updated_by_id = None
    user.mfa_secret = None
    user.last_login_at = None
    user.to_audit_dict.return_value = {
        "id": "user-abc-123",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "created_by_id": None,
        "updated_by_id": None,
    }
    return user


@pytest.fixture()
def mock_pref() -> MagicMock:
    pref = MagicMock()
    pref.id = "pref-123"
    pref.user_id = "user-abc-123"
    from app.enums import ThemePreference, DashboardLayout
    pref.theme = ThemePreference.SYSTEM
    pref.timezone = "UTC"
    pref.language = "en"
    pref.dashboard_layout = DashboardLayout.OVERVIEW
    pref.items_per_page = 25
    pref.default_booking_channel = "web"
    pref.show_ticket_cost_column = True
    pref.auto_send_confirmation = True
    pref.notify_new_booking = True
    pref.notify_payment_received = True
    pref.notify_booking_cancelled = True
    pref.notify_booking_confirmed = True
    pref.notify_new_client = True
    pref.notify_referral_qualified = True
    pref.notify_subscription_renewal = True
    pref.notify_low_stock_alert = True
    from datetime import datetime
    pref.created_at = datetime(2024, 1, 1)
    pref.updated_at = datetime(2024, 1, 1)
    pref.created_by_id = None
    pref.updated_by_id = None
    pref.to_audit_dict.return_value = {
        "id": "pref-123",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "created_by_id": None,
        "updated_by_id": None,
    }
    return pref


# ── Tests: Get & List ──────────────────────────────────────────────────────────

def test_get_user_success(service, user_repo, mock_user):
    user_repo.get.return_value = mock_user

    result = service.get_user("user-abc-123")

    assert result.id == "user-abc-123"
    assert result.email == "test@thrive.com"
    user_repo.get.assert_called_once_with("user-abc-123")


def test_get_user_by_email_success(service, user_repo, mock_user):
    user_repo.find_by_email.return_value = mock_user

    result = service.get_user_by_email(" TEST@Thrive.com ")

    assert result.email == "test@thrive.com"
    user_repo.find_by_email.assert_called_once_with("test@thrive.com")


def test_get_user_by_email_not_found(service, user_repo):
    user_repo.find_by_email.return_value = None

    with pytest.raises(NotFoundError):
        service.get_user_by_email("ghost@thrive.com")


def test_list_users(service, user_repo, mock_user):
    page_mock = MagicMock()
    page_mock.items = [mock_user]
    page_mock.total = 1
    page_mock.page = 1
    page_mock.per_page = 25
    page_mock.total_pages = 1
    page_mock.has_next = False
    page_mock.has_prev = False

    user_repo.paginate_users.return_value = page_mock

    result = service.list_users(role=UserRole.AGENT, page=1, per_page=25)

    assert len(result["items"]) == 1
    assert result["items"][0].id == "user-abc-123"
    assert result["total"] == 1
    assert result["has_next"] is False
    user_repo.paginate_users.assert_called_once_with(
        role=UserRole.AGENT,
        is_active=None,
        search=None,
        page=1,
        per_page=25,
    )


# ── Tests: Create ──────────────────────────────────────────────────────────────

@patch("app.interface.user.services.event_bus")
@patch("app.interface.user.services.hash_password", return_value="HASHED")
def test_create_user_success(mock_hash, mock_bus, service, user_repo, user_preference_repo, audit_service, uow, mock_user):
    user_repo.exists.return_value = False
    user_repo.create.return_value = mock_user
    
    req = UserCreateRequest.model_validate({
        "email": "NEW@Thrive.com",
        "full_name": "New User",
        "phone": "0799999999",
        "password": "Password1!",
        "role": UserRole.AGENT.value,
    })

    result = service.create_user(req, actor_id="admin-123")

    assert result.email == "test@thrive.com"
    user_repo.exists.assert_called_with(email="new@thrive.com")
    user_repo.create.assert_called_once_with(
        actor_id="admin-123",
        email="new@thrive.com",
        full_name="New User",
        phone="0799999999",
        password_hash="HASHED",
        role=UserRole.AGENT,
        is_active=True,
    )
    user_preference_repo.get_or_create.assert_called_once_with(user_id="user-abc-123", actor_id="admin-123")
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], UserCreatedEvent)


def test_create_user_duplicate_email(service, user_repo):
    user_repo.exists.return_value = True

    req = UserCreateRequest.model_validate({
        "email": "existing@thrive.com",
        "full_name": "Existing User",
        "phone": "0799999999",
        "password": "Password1!",
        "role": UserRole.AGENT.value,
    })

    with pytest.raises(DuplicateEmailError):
        service.create_user(req, actor_id="admin-123")


# ── Tests: Update ──────────────────────────────────────────────────────────────

@patch("app.interface.user.services.event_bus")
def test_update_user_success(mock_bus, service, user_repo, audit_service, uow, mock_user):
    user_repo.get.return_value = mock_user

    req = UserUpdateRequest.model_validate({
        "full_name": "Updated Name"
    })

    result = service.update_user("user-abc-123", req, actor_id="admin-123")

    assert result.id == "user-abc-123"
    user_repo.update.assert_called_once_with(mock_user, actor_id="admin-123", full_name="Updated Name")
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], UserUpdatedEvent)


# ── Tests: Deactivate & Reactivate ─────────────────────────────────────────────

@patch("app.interface.user.services.event_bus")
def test_deactivate_user_success(mock_bus, service, user_repo, audit_service, uow, mock_user):
    user_repo.get.return_value = mock_user

    result = service.deactivate_user("user-abc-123", actor_id="admin-123")

    user_repo.update.assert_called_once_with(mock_user, actor_id="admin-123", is_active=False)
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()


def test_deactivate_last_super_admin(service, user_repo, mock_user):
    mock_user.role = UserRole.SUPER_ADMIN
    user_repo.get.return_value = mock_user
    user_repo.find_active_by_role.return_value = [mock_user]  # Only 1 active

    with pytest.raises(BadRequestError):
        service.deactivate_user("user-abc-123", actor_id="admin-123")


@patch("app.interface.user.services.event_bus")
def test_reactivate_user_success(mock_bus, service, user_repo, audit_service, uow, mock_user):
    mock_user.is_active = False
    user_repo.get.return_value = mock_user

    result = service.reactivate_user("user-abc-123", actor_id="admin-123")

    user_repo.update.assert_called_once_with(mock_user, actor_id="admin-123", is_active=True)
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], UserReactivatedEvent)


# ── Tests: Preferences ─────────────────────────────────────────────────────────

def test_get_preference_success(service, user_repo, user_preference_repo, uow, mock_user, mock_pref):
    user_repo.get.return_value = mock_user
    user_preference_repo.get_or_create.return_value = mock_pref

    result = service.get_preference("user-abc-123")

    assert result.language == "en"
    user_preference_repo.get_or_create.assert_called_once_with(user_id="user-abc-123")
    assert uow.committed == 1


@patch("app.interface.user.services.event_bus")
def test_update_preference_success(mock_bus, service, user_repo, user_preference_repo, uow, mock_user, mock_pref):
    user_repo.get.return_value = mock_user
    user_preference_repo.get_or_create.return_value = mock_pref

    req = UserPreferenceUpdateRequest.model_validate({
        "language": "es"
    })

    result = service.update_preference("user-abc-123", req, actor_id="admin-123")

    user_preference_repo.update.assert_called_once_with(mock_pref, actor_id="admin-123", language="es")
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], UserPreferenceUpdatedEvent)
