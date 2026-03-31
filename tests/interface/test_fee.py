"""
Unit tests for FeeService.

Uses exact mocking patterns mapping the CQRS structural splits natively
without hitting the database integrations natively.
"""

from __future__ import annotations

from decimal import Decimal
import pytest
from unittest.mock import MagicMock, patch

from app.core.unit_of_work import IUnitOfWork
from app.core.errors.handlers import BadRequestError, NotFoundError
from app.enums import FeeType, BookingChannel
from app.dto import (
    ServiceFeeCreateRequest,
    ServiceFeeScheduleCreateRequest,
)
from app.interface.fee import FeeService
from app.core.events.dataclass.fee import (
    FeeScheduleCreatedEvent,
    FeeScheduleActivatedEvent,
    FeeScheduleDeactivatedEvent,
    ServiceFeeAddedEvent,
    ServiceFeeUpdatedEvent,
    ServiceFeeDeactivatedEvent,
    FeeSnapshotCreatedEvent,
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
def fee_schedule_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def fee_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def fee_snapshot_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def audit_service() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def service(
    fee_schedule_repo,
    fee_repo,
    fee_snapshot_repo,
    audit_service,
    uow
) -> FeeService:
    return FeeService(
        fee_schedule_repo=fee_schedule_repo,
        fee_repo=fee_repo,
        fee_snapshot_repo=fee_snapshot_repo,
        audit_service=audit_service,
        uow=uow,
    )


@pytest.fixture()
def mock_fee() -> MagicMock:
    fee = MagicMock()
    fee.id = "fee-123"
    fee.schedule_id = "sch-123"
    fee.fee_type = FeeType.DOMESTIC_FLIGHT
    fee.label = "Domestic Fee"
    fee.amount_usd = Decimal("15.00")
    fee.min_amount_usd = None
    fee.max_amount_usd = None
    fee.is_per_passenger = True
    fee.is_percentage = False
    fee.is_active = True
    
    from datetime import datetime, timezone
    fee.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    fee.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    fee.created_by_id = None
    fee.updated_by_id = None
    
    return fee

@pytest.fixture()
def mock_surcharge() -> MagicMock:
    fee = MagicMock()
    fee.id = "fee-sur"
    fee.fee_type = FeeType.EMERGENCY_SURCHARGE
    fee.amount_usd = Decimal("25.00")
    fee.is_per_passenger = False
    return fee

@pytest.fixture()
def mock_schedule(mock_fee) -> MagicMock:
    sch = MagicMock()
    sch.id = "sch-123"
    sch.name = "Standard 2024"
    sch.description = "Base pricing"
    sch.is_active = True
    sch.fees = [mock_fee]

    from datetime import datetime, timezone
    sch.effective_from = datetime(2024, 1, 1, tzinfo=timezone.utc)
    sch.effective_to = None

    sch.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    sch.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    sch.created_by_id = None
    sch.updated_by_id = None
    
    return sch


# ── Tests: Queries ───────────────────────────────────────────────────────────

def test_get_active_schedule_success(service, fee_schedule_repo, mock_schedule):
    fee_schedule_repo.find_active.return_value = mock_schedule
    result = service.get_active_schedule()

    assert result.id == "sch-123"
    assert result.name == "Standard 2024"
    assert len(result.fees) == 1
    fee_schedule_repo.find_active.assert_called_once()


def test_get_active_schedule_not_found(service, fee_schedule_repo):
    fee_schedule_repo.find_active.return_value = None
    with pytest.raises(NotFoundError):
        service.get_active_schedule()


def test_list_schedules(service, fee_schedule_repo, mock_schedule):
    page_mock = MagicMock()
    page_mock.items = [mock_schedule]
    page_mock.total = 1
    page_mock.page = 1
    page_mock.per_page = 25
    page_mock.total_pages = 1
    page_mock.has_next = False
    page_mock.has_prev = False

    fee_schedule_repo.paginate.return_value = page_mock

    result = service.list_schedules(page=1, per_page=25)
    assert len(result["items"]) == 1
    assert result["items"][0].id == "sch-123"
    assert result["total"] == 1


# ── Tests: Schedule Mutations ────────────────────────────────────────────────

@patch("app.interface.fee.services.event_bus")
def test_create_schedule_success(
    mock_bus, service, fee_schedule_repo, fee_repo, audit_service, uow, mock_schedule
):
    fee_schedule_repo.create.return_value = mock_schedule

    req = ServiceFeeScheduleCreateRequest.model_validate({
        "name": "Standard 2025",
        "description": "Base",
        "effective_from": "2025-01-01T00:00:00Z",
        "fees": [
            {
                "fee_type": FeeType.DOMESTIC_FLIGHT,
                "label": "Flight",
                "amount_usd": "20.00",
                "is_per_passenger": True,
                "is_percentage": False
            }
        ]
    })

    result = service.create_schedule(req, actor_id="admin-1")

    fee_schedule_repo.create.assert_called_once()
    fee_repo.create.assert_called_once()
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], FeeScheduleCreatedEvent)


@patch("app.interface.fee.services.event_bus")
def test_activate_schedule(
    mock_bus, service, fee_schedule_repo, audit_service, uow, mock_schedule
):
    fee_schedule_repo.get.return_value = mock_schedule

    result = service.activate_schedule("sch-123", actor_id="admin-1")

    fee_schedule_repo.deactivate_all.assert_called_once_with(actor_id="admin-1")
    fee_schedule_repo.update.assert_called_once_with(mock_schedule, actor_id="admin-1", is_active=True)
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], FeeScheduleActivatedEvent)


@patch("app.interface.fee.services.event_bus")
def test_deactivate_schedule_success(
    mock_bus, service, fee_schedule_repo, audit_service, uow, mock_schedule
):
    fee_schedule_repo.get.return_value = mock_schedule
    fee_schedule_repo.count.return_value = 2  # more than 1 active

    service.deactivate_schedule("sch-123", actor_id="admin-1")

    fee_schedule_repo.update.assert_called_once_with(mock_schedule, actor_id="admin-1", is_active=False)
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], FeeScheduleDeactivatedEvent)


def test_deactivate_last_active_schedule_fails(
    service, fee_schedule_repo, mock_schedule
):
    fee_schedule_repo.get.return_value = mock_schedule
    fee_schedule_repo.count.return_value = 1  # Only 1 active

    with pytest.raises(BadRequestError):
        service.deactivate_schedule("sch-123", actor_id="admin-1")


# ── Tests: Fee Mutations ─────────────────────────────────────────────────────

@patch("app.interface.fee.services.event_bus")
def test_add_fee_to_schedule(
    mock_bus, service, fee_schedule_repo, fee_repo, uow, mock_fee
):
    fee_schedule_repo.get.return_value = MagicMock()
    fee_repo.create.return_value = mock_fee

    req = ServiceFeeCreateRequest.model_validate({
        "fee_type": FeeType.DOMESTIC_FLIGHT,
        "label": "Extra Fee",
        "amount_usd": "10.00",
        "is_per_passenger": True,
        "is_percentage": False
    })

    result = service.add_fee_to_schedule("sch-123", req, actor_id="admin-1")

    fee_repo.create.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], ServiceFeeAddedEvent)


@patch("app.interface.fee.services.event_bus")
def test_update_fee(mock_bus, service, fee_repo, uow, mock_fee):
    fee_repo.get.return_value = mock_fee

    result = service.update_fee("fee-123", {"amount_usd": Decimal("20.00")}, actor_id="admin-1")

    fee_repo.update.assert_called_once_with(mock_fee, actor_id="admin-1", amount_usd=Decimal("20.00"))
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], ServiceFeeUpdatedEvent)


@patch("app.interface.fee.services.event_bus")
def test_deactivate_fee(mock_bus, service, fee_repo, uow, mock_fee):
    fee_repo.get.return_value = mock_fee

    service.deactivate_fee("fee-123", actor_id="admin-1")

    fee_repo.update.assert_called_once_with(mock_fee, actor_id="admin-1", is_active=False)
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], ServiceFeeDeactivatedEvent)


# ── Tests: Fee Resolution ────────────────────────────────────────────────────

def test_resolve_fee_success(service, fee_repo, mock_fee):
    fee_repo.find_active_by_type.return_value = mock_fee  # amounts to 15.00

    amount = service.resolve_fee(FeeType.DOMESTIC_FLIGHT, num_passengers=2, is_emergency=False)

    assert amount == Decimal("30.00")


def test_resolve_fee_emergency(service, fee_repo, mock_fee, mock_surcharge):
    def side_effect(fee_type):
        if fee_type == FeeType.DOMESTIC_FLIGHT:
            return mock_fee
        if fee_type == FeeType.EMERGENCY_SURCHARGE:
            return mock_surcharge
        return None
        
    fee_repo.find_active_by_type.side_effect = side_effect

    amount = service.resolve_fee(FeeType.DOMESTIC_FLIGHT, num_passengers=1, is_emergency=True)

    # 15.00 for flight + 25.00 for emergency mapping = 40.00
    assert amount == Decimal("40.00")


# ── Tests: Snapshots ─────────────────────────────────────────────────────────

@patch("app.interface.fee.services.event_bus")
def test_create_snapshot(mock_bus, service, fee_repo, fee_snapshot_repo, uow, mock_fee):
    fee_repo.get.return_value = mock_fee
    
    mock_snapshot = MagicMock()
    mock_snapshot.id = "snap-123"
    mock_snapshot.booking_id = "book-123"
    mock_snapshot.fee_id = "fee-123"
    mock_snapshot.fee_type = mock_fee.fee_type
    mock_snapshot.fee_label = mock_fee.label
    mock_snapshot.base_amount_usd = mock_fee.amount_usd
    mock_snapshot.applied_amount_usd = Decimal("15.00")
    mock_snapshot.num_passengers = 1
    mock_snapshot.channel = BookingChannel.WHATSAPP
    mock_snapshot.emergency_surcharge_applied = False
    
    from datetime import datetime, timezone
    mock_snapshot.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    mock_snapshot.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    mock_snapshot.created_by_id = None
    mock_snapshot.updated_by_id = None
    fee_snapshot_repo.create.return_value = mock_snapshot

    result = service.create_snapshot(
        booking_id="book-123",
        fee_id="fee-123",
        applied_amount=Decimal("15.00"),
        num_passengers=1,
        channel=BookingChannel.WHATSAPP,
        emergency=False,
        actor_id="admin-1"
    )

    fee_snapshot_repo.create.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()
    assert isinstance(mock_bus.publish.call_args[0][0], FeeSnapshotCreatedEvent)
