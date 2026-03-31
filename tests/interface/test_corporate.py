"""
Unit tests for CorporateService.

Uses exact mocking patterns matching ClientService scaling, deploying FakeUoW
to decouple native SQLAlchemy dependency injections.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch

from app.core.unit_of_work import IUnitOfWork
from app.core.errors.handlers import (
    NotFoundError,
    SubscriptionLimitError,
)
from app.enums import SubscriptionTier
from app.dto import (
    CorporateAccountCreateRequest,
    CorporateAccountUpdateRequest,
    CorporateSubscriptionCreateRequest,
)
from app.interface.corporate import CorporateService
from app.core.events.dataclass.corporate import (
    CorporateAccountCreatedEvent,
    CorporateAccountUpdatedEvent,
    CorporateAccountDeactivatedEvent,
    SubscriptionCreatedEvent,
    SubscriptionUpgradedEvent,
    SubscriptionRenewedEvent,
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
def corporate_account_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def corporate_subscription_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def client_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def audit_service() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def service(
    corporate_account_repo,
    corporate_subscription_repo,
    client_repo,
    audit_service,
    uow
) -> CorporateService:
    return CorporateService(
        corporate_account_repo=corporate_account_repo,
        corporate_subscription_repo=corporate_subscription_repo,
        client_repo=client_repo,
        audit_service=audit_service,
        uow=uow,
    )


@pytest.fixture()
def mock_sub() -> MagicMock:
    sub = MagicMock()
    sub.id = "sub-123"
    sub.account_id = "corp-123"
    sub.tier = SubscriptionTier.BRONZE
    sub.monthly_fee = Decimal("150.00")
    sub.bookings_limit = 6
    sub.bookings_used = 2
    sub.concierge_247 = False
    
    # Must use explicit methods for evaluation properties inside models
    sub.is_at_limit.return_value = False
    
    from datetime import timezone
    sub.billing_cycle_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    sub.billing_cycle_end = datetime(2024, 2, 1, tzinfo=timezone.utc)
    sub.is_active = True

    sub.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    sub.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    sub.created_by_id = None
    sub.updated_by_id = None
    
    sub.to_audit_dict.return_value = {"id": "sub-123"}
    return sub


@pytest.fixture()
def mock_account(mock_sub) -> MagicMock:
    acc = MagicMock()
    acc.id = "corp-123"
    acc.company_name = "Thrive Corp"
    acc.registration_number = "123456"
    acc.industry = "Tech"
    acc.website = "https://thrive.io"
    acc.billing_email = "billing@thrive.io"
    acc.billing_address = "123 Tech Ave"
    acc.contact_person_id = None
    acc.is_active = True
    acc.subscription = mock_sub
    acc.tax_id = None
    acc.primary_contact_name = None
    acc.primary_contact_phone = None

    from datetime import timezone
    acc.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    acc.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    acc.created_by_id = None
    acc.updated_by_id = None
    
    acc.to_audit_dict.return_value = {"id": "corp-123", "company_name": "Thrive Corp", "billing_email": "billing@thrive.io"}
    return acc


# ── Tests: Account Queries ───────────────────────────────────────────────────

def test_get_corporate_account_success(service, corporate_account_repo, client_repo, mock_account):
    corporate_account_repo.get.return_value = mock_account
    client_repo.find_by_corporate_account.return_value = [MagicMock(), MagicMock()] # 2 clients

    result = service.get_corporate_account("corp-123")
    
    assert result.id == "corp-123"
    assert result.client_count == 2
    assert result.subscription is not None
    assert result.subscription.tier == SubscriptionTier.BRONZE
    assert result.subscription.bookings_remaining == 4


def test_list_corporate_accounts(service, corporate_account_repo, mock_account):
    page_mock = MagicMock()
    page_mock.items = [mock_account]
    page_mock.total = 1
    page_mock.page = 1
    page_mock.per_page = 25
    page_mock.total_pages = 1
    page_mock.has_next = False
    page_mock.has_prev = False

    corporate_account_repo.paginate_accounts.return_value = page_mock

    result = service.list_corporate_accounts(page=1, per_page=25)

    assert len(result["items"]) == 1
    assert result["items"][0].id == "corp-123"
    assert result["total"] == 1


# ── Tests: Account Mutations ─────────────────────────────────────────────────

@patch("app.interface.corporate.services.event_bus")
def test_create_corporate_account_success(
    mock_bus, service, corporate_account_repo, client_repo, audit_service, uow, mock_account
):
    corporate_account_repo.create.return_value = mock_account
    corporate_account_repo.get.return_value = mock_account
    client_repo.find_by_corporate_account.return_value = []

    req = CorporateAccountCreateRequest.model_validate({
        "company_name": "Thrive Corp",
        "billing_email": "billing@thrive.io",
    })

    result = service.create_corporate_account(req, actor_id="admin-1")

    corporate_account_repo.create.assert_called_once_with(
        actor_id="admin-1",
        company_name="Thrive Corp",
        billing_email="billing@thrive.io",
        industry=None,
        billing_address=None,
        tax_id=None,
        primary_contact_name=None,
        primary_contact_phone=None,
    )
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], CorporateAccountCreatedEvent)


@patch("app.interface.corporate.services.event_bus")
def test_update_corporate_account_success(
    mock_bus, service, corporate_account_repo, client_repo, audit_service, uow, mock_account
):
    corporate_account_repo.get.return_value = mock_account
    client_repo.find_by_corporate_account.return_value = []

    req = CorporateAccountUpdateRequest.model_validate({
        "industry": "Finance"
    })

    result = service.update_corporate_account("corp-123", req, actor_id="admin-1")

    corporate_account_repo.update.assert_called_once_with(mock_account, actor_id="admin-1", industry="Finance")
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], CorporateAccountUpdatedEvent)


@patch("app.interface.corporate.services.event_bus")
def test_deactivate_corporate_account(
    mock_bus, service, corporate_account_repo, corporate_subscription_repo, audit_service, uow, mock_account
):
    corporate_account_repo.get.return_value = mock_account

    service.deactivate_corporate_account("corp-123", actor_id="admin-1")

    corporate_account_repo.update.assert_called_once_with(mock_account, actor_id="admin-1", is_active=False)
    corporate_subscription_repo.update.assert_called_once_with(
        mock_account.subscription, actor_id="admin-1", is_active=False
    )
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], CorporateAccountDeactivatedEvent)


# ── Tests: Subscription Mutations ─────────────────────────────────────────────

@patch("app.interface.corporate.services.event_bus")
def test_create_subscription_success(
    mock_bus, service, corporate_account_repo, corporate_subscription_repo, audit_service, uow, mock_account, mock_sub
):
    corporate_account_repo.exists.return_value = True
    corporate_subscription_repo.find_by_account.return_value = None
    corporate_subscription_repo.create.return_value = mock_sub

    req = CorporateSubscriptionCreateRequest.model_validate({
        "account_id": "corp-123",
        "tier": SubscriptionTier.SILVER,
        "monthly_fee": "300.00",
        "billing_cycle_start": "2024-01-01T00:00:00Z",
        "billing_cycle_end": "2024-02-01T00:00:00Z",
    })

    result = service.create_subscription(req, actor_id="admin-1")

    corporate_subscription_repo.create.assert_called_once()
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], SubscriptionCreatedEvent)


@patch("app.interface.corporate.services.event_bus")
def test_upgrade_subscription_success(
    mock_bus, service, corporate_account_repo, corporate_subscription_repo, audit_service, uow, mock_account, mock_sub
):
    corporate_account_repo.get.return_value = mock_account
    corporate_subscription_repo.find_by_account.return_value = mock_sub
    corporate_subscription_repo.create.return_value = mock_sub

    result = service.upgrade_subscription("corp-123", SubscriptionTier.GOLD, actor_id="admin-1")

    corporate_subscription_repo.update.assert_called_once_with(mock_sub, actor_id="admin-1", is_active=False)
    corporate_subscription_repo.create.assert_called_once()
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], SubscriptionUpgradedEvent)


@patch("app.interface.corporate.services.event_bus")
def test_renew_subscription_success(
    mock_bus, service, corporate_subscription_repo, audit_service, uow, mock_sub
):
    corporate_subscription_repo.find_by_account.return_value = mock_sub

    result = service.renew_subscription("corp-123", actor_id="admin-1")

    corporate_subscription_repo.reset_billing_cycle.assert_called_once()
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], SubscriptionRenewedEvent)


def test_renew_subscription_not_found(service, corporate_subscription_repo):
    corporate_subscription_repo.find_by_account.return_value = None

    with pytest.raises(NotFoundError):
        service.renew_subscription("corp-ghost", actor_id="admin-1")


# ── Tests: Bookings Limits ───────────────────────────────────────────────────

def test_check_booking_allowance_success(service, corporate_subscription_repo, mock_sub):
    corporate_subscription_repo.find_by_account.return_value = mock_sub
    
    assert service.check_booking_allowance("corp-123") is True


def test_check_booking_allowance_limit_reached(service, corporate_subscription_repo, mock_sub):
    mock_sub.is_at_limit.return_value = True
    corporate_subscription_repo.find_by_account.return_value = mock_sub
    
    with pytest.raises(SubscriptionLimitError):
        service.check_booking_allowance("corp-123")


def test_increment_booking_usage(service, corporate_subscription_repo, uow, mock_sub):
    corporate_subscription_repo.find_by_account.return_value = mock_sub

    service.increment_booking_usage("corp-123", actor_id="admin-1")

    corporate_subscription_repo.increment_bookings_used.assert_called_once_with(mock_sub, actor_id="admin-1")
    assert uow.committed == 1
