"""
Unit tests for ClientService.

Provides identical coverage structures over isolated components 
mirroring UserService test mechanics with FakeUoW.
"""
from __future__ import annotations

from decimal import Decimal
import pytest
from unittest.mock import MagicMock, patch

from app.core.unit_of_work import IUnitOfWork
from app.core.errors.handlers import (
    DuplicateEmailError,
    NotFoundError,
    BadRequestError,
)
from app.enums import ClientType, BookingStatus
from app.dto import (
    ClientCreateRequest,
    ClientUpdateRequest,
    ClientPreferenceUpdateRequest,
)
from app.interface.client import ClientService
from app.core.events.dataclass.client import (
    ClientCreatedEvent,
    ClientUpdatedEvent,
    ClientDeactivatedEvent,
    ClientPreferenceUpdatedEvent,
)


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
def client_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def client_preference_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def booking_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def loyalty_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def audit_service() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def service(
    client_repo,
    client_preference_repo,
    booking_repo,
    loyalty_repo,
    audit_service,
    uow
) -> ClientService:
    return ClientService(
        client_repo=client_repo,
        client_preference_repo=client_preference_repo,
        booking_repo=booking_repo,
        loyalty_repo=loyalty_repo,
        audit_service=audit_service,
        uow=uow,
    )


@pytest.fixture()
def mock_client() -> MagicMock:
    client = MagicMock()
    client.id = "client-123"
    client.email = "client@thrive.com"
    client.first_name = "Jane"
    client.last_name = "Doe"
    client.full_name = "Jane Doe"
    client.phone = "0790000000"
    client.whatsapp_number = None
    client.preferred_language = "en"
    client.nationality = None
    client.passport_expiry = None
    client.date_of_birth = None
    client.notes = None
    client.is_group_leader = False
    client.client_type = ClientType.INDIVIDUAL
    client.corporate_account_id = None
    client.is_active = True
    client.referred_by_id = None
    
    from decimal import Decimal
    client.loyalty_balance_usd = Decimal("0.00")
    client.total_bookings = 0
    
    from datetime import datetime
    client.created_at = datetime(2024, 1, 1)
    client.updated_at = datetime(2024, 1, 1)
    client.created_by_id = None
    client.updated_by_id = None
    client.to_audit_dict.return_value = {
        "id": "client-123",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "created_by_id": None,
        "updated_by_id": None,
    }
    return client


@pytest.fixture()
def mock_pref() -> MagicMock:
    pref = MagicMock()
    pref.id = "pref-123"
    pref.client_id = "client-123"
    from app.enums import PreferredChannel, DocumentFormat
    pref.preferred_channel = PreferredChannel.EMAIL
    pref.preferred_document_format = DocumentFormat.PDF
    pref.marketing_opt_in = True
    pref.booking_reminders = True
    pref.travel_reminder_hours = 24
    pref.payment_reminders = True
    pref.language = "en"
    pref.preferred_currency_display = "USD"
    pref.timezone = "UTC"

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

def test_get_client_success(service, client_repo, booking_repo, loyalty_repo, mock_client):
    client_repo.get.return_value = mock_client
    loyalty_repo.balance_for_client.return_value = Decimal("100.00")
    booking_repo.count.return_value = 5

    result = service.get_client("client-123")

    assert result.id == "client-123"
    assert result.loyalty_balance_usd == Decimal("100.00")
    assert result.total_bookings == 5
    client_repo.get.assert_called_once_with("client-123")


def test_get_client_by_email_success(service, client_repo, booking_repo, loyalty_repo, mock_client):
    client_repo.find_by_email.return_value = mock_client
    client_repo.get.return_value = mock_client
    loyalty_repo.balance_for_client.return_value = Decimal("100.00")
    booking_repo.count.return_value = 5

    result = service.get_client_by_email(" Client@Thrive.com ")

    assert result.email == "client@thrive.com"
    client_repo.find_by_email.assert_called_once_with("client@thrive.com")


def test_get_client_by_email_not_found(service, client_repo):
    client_repo.find_by_email.return_value = None

    with pytest.raises(NotFoundError):
        service.get_client_by_email("ghost@thrive.com")


def test_list_clients(service, client_repo, mock_client):
    page_mock = MagicMock()
    page_mock.items = [mock_client]
    page_mock.total = 1
    page_mock.page = 1
    page_mock.per_page = 25
    page_mock.total_pages = 1
    page_mock.has_next = False
    page_mock.has_prev = False

    client_repo.paginate_clients.return_value = page_mock

    result = service.list_clients(client_type=ClientType.INDIVIDUAL, page=1, per_page=25)

    assert len(result["items"]) == 1
    assert result["items"][0].id == "client-123"
    assert result["total"] == 1


# ── Tests: Create ──────────────────────────────────────────────────────────────

@patch("app.interface.client.services.event_bus")
def test_create_client_success(
    mock_bus,
    service,
    client_repo,
    client_preference_repo,
    booking_repo,
    loyalty_repo,
    audit_service,
    uow,
    mock_client
):
    client_repo.find_by_email.return_value = None
    client_repo.create.return_value = mock_client
    client_repo.get.return_value = mock_client
    loyalty_repo.balance_for_client.return_value = Decimal("0.00")
    booking_repo.count.return_value = 0
    
    req = ClientCreateRequest.model_validate({
        "first_name": "New",
        "last_name": "Client",
        "email": "NEW@Thrive.com",
        "phone": "0799999999",
        "client_type": ClientType.INDIVIDUAL,
    })

    result = service.create_client(req, actor_id="admin-123")

    # Assuming get_client runs successfully (loyalty/bookings mocked automatically returns MagicMock or handles it)
    client_repo.find_by_email.assert_called_with("new@thrive.com")
    client_repo.create.assert_called_once_with(
        actor_id="admin-123",
        email="new@thrive.com",
        first_name="New",
        last_name="Client",
        phone="0799999999",
        whatsapp_number=None,
        nationality=None,
        passport_number=None,
        passport_expiry=None,
        date_of_birth=None,
        preferred_language="en",
        client_type=ClientType.INDIVIDUAL,
        corporate_account_id=None,
        referred_by_id=None,
        notes=None,
    )
    client_preference_repo.get_or_create.assert_called_once_with(client_id="client-123", actor_id="admin-123")
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], ClientCreatedEvent)


def test_create_client_duplicate_email(service, client_repo):
    client_repo.find_by_email.return_value = True

    req = ClientCreateRequest.model_validate({
        "first_name": "Existing",
        "last_name": "Client",
        "email": "existing@thrive.com",
    })

    with pytest.raises(DuplicateEmailError):
        service.create_client(req, actor_id="admin-123")


# ── Tests: Update ──────────────────────────────────────────────────────────────

@patch("app.interface.client.services.event_bus")
def test_update_client_success(mock_bus, service, client_repo, booking_repo, loyalty_repo, audit_service, uow, mock_client):
    client_repo.get.return_value = mock_client
    loyalty_repo.balance_for_client.return_value = Decimal("0.00")
    booking_repo.count.return_value = 0

    req = ClientUpdateRequest.model_validate({
        "first_name": "Updated"
    })

    result = service.update_client("client-123", req, actor_id="admin-123")

    client_repo.update.assert_called_once_with(mock_client, actor_id="admin-123", first_name="Updated")
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], ClientUpdatedEvent)


# ── Tests: Deactivate ──────────────────────────────────────────────────────────

@patch("app.interface.client.services.event_bus")
def test_deactivate_client_success(mock_bus, service, client_repo, booking_repo, loyalty_repo, audit_service, uow, mock_client):
    client_repo.get.return_value = mock_client
    booking_repo.find_by_client.return_value = [] # No active bookings
    loyalty_repo.balance_for_client.return_value = Decimal("0.00")
    booking_repo.count.return_value = 0

    result = service.deactivate_client("client-123", actor_id="admin-123")

    client_repo.update.assert_called_once_with(mock_client, actor_id="admin-123", is_active=False)
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], ClientDeactivatedEvent)


def test_deactivate_client_active_bookings(service, client_repo, booking_repo, mock_client):
    client_repo.get.return_value = mock_client
    # Simulate first status check returning a booking
    booking_repo.find_by_client.return_value = [MagicMock()]

    with pytest.raises(BadRequestError):
        service.deactivate_client("client-123", actor_id="admin-123")


# ── Tests: Preferences ─────────────────────────────────────────────────────────

def test_get_client_preference_success(service, client_repo, client_preference_repo, uow, mock_client, mock_pref):
    client_repo.exists.return_value = True
    client_preference_repo.get_or_create.return_value = mock_pref

    result = service.get_client_preference("client-123")

    assert result.language == "en"
    client_preference_repo.get_or_create.assert_called_once_with(client_id="client-123")
    assert uow.committed == 1


@patch("app.interface.client.services.event_bus")
def test_update_client_preference(mock_bus, service, client_repo, client_preference_repo, uow, mock_client, mock_pref):
    client_repo.exists.return_value = True
    client_preference_repo.get_or_create.return_value = mock_pref

    req = ClientPreferenceUpdateRequest.model_validate({
        "language": "es"
    })

    result = service.update_client_preference("client-123", req, actor_id="admin-123")

    client_preference_repo.update.assert_called_once_with(mock_pref, actor_id="admin-123", language="es")
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], ClientPreferenceUpdatedEvent)
