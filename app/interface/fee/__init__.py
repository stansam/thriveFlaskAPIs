# app/interface/fee/__init__.py
"""
FeeService Facade.

Composes separated CQRS-like operations framing
the complete Service Fee boundaries natively.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.enums import FeeType, BookingChannel
from app.dto import (
    ServiceFeeCreateRequest,
    ServiceFeeResponse,
    ServiceFeeScheduleCreateRequest,
    ServiceFeeScheduleResponse,
    ServiceFeeSnapshotResponse,
)

from app.interface.fee.services import (
    GetActiveScheduleOperation,
    ListSchedulesOperation,
    CreateScheduleOperation,
    ActivateScheduleOperation,
    DeactivateScheduleOperation,
    AddFeeToScheduleOperation,
    UpdateFeeOperation,
    DeactivateFeeOperation,
    ResolveFeeOperation,
    CreateSnapshotOperation,
)

from app.repository.fee import ServiceFeeScheduleRepository, ServiceFeeRepository, ServiceFeeSnapshotRepository
from app.interface.audit import AuditService
from app.core.unit_of_work import IUnitOfWork


class FeeService:
    """Service handling schedules, fee resolutions and immutable snapshots.

    Responsibilities
    ----------------
    - Querying active corporate thresholds securely.
    - Encapsulating immutable pricing snapshots.
    - Transactional mapping enforcing Strict audits gracefully natively.
    """

    def __init__(
        self,
        fee_schedule_repo: ServiceFeeScheduleRepository,
        fee_repo: ServiceFeeRepository,
        fee_snapshot_repo: ServiceFeeSnapshotRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
    ) -> None:
        args = (fee_schedule_repo, fee_repo, fee_snapshot_repo, audit_service, uow)
        
        self._get_active_op = GetActiveScheduleOperation(*args)
        self._list_op = ListSchedulesOperation(*args)
        self._create_op = CreateScheduleOperation(*args)
        self._activate_op = ActivateScheduleOperation(*args)
        self._deactivate_op = DeactivateScheduleOperation(*args)
        self._add_fee_op = AddFeeToScheduleOperation(*args)
        self._update_fee_op = UpdateFeeOperation(*args)
        self._deactivate_fee_op = DeactivateFeeOperation(*args)
        self._resolve_fee_op = ResolveFeeOperation(*args)
        self._create_snapshot_op = CreateSnapshotOperation(*args)

    # Queries
    def get_active_schedule(self) -> ServiceFeeScheduleResponse:
        return self._get_active_op.execute()

    def list_schedules(self, page: int = 1, per_page: int = 25) -> dict[str, Any]:
        return self._list_op.execute(page, per_page)

    # Schedule mutations
    def create_schedule(
        self, data: ServiceFeeScheduleCreateRequest, actor_id: str
    ) -> ServiceFeeScheduleResponse:
        return self._create_op.execute(data, actor_id)

    def activate_schedule(self, schedule_id: str, actor_id: str) -> ServiceFeeScheduleResponse:
        return self._activate_op.execute(schedule_id, actor_id)

    def deactivate_schedule(self, schedule_id: str, actor_id: str) -> None:
        self._deactivate_op.execute(schedule_id, actor_id)

    # Fee mutations
    def add_fee_to_schedule(
        self, schedule_id: str, data: ServiceFeeCreateRequest, actor_id: str
    ) -> ServiceFeeResponse:
        return self._add_fee_op.execute(schedule_id, data, actor_id)

    def update_fee(self, fee_id: str, data: dict[str, Any], actor_id: str) -> ServiceFeeResponse:
        return self._update_fee_op.execute(fee_id, data, actor_id)

    def deactivate_fee(self, fee_id: str, actor_id: str) -> None:
        self._deactivate_fee_op.execute(fee_id, actor_id)

    # Fee resolution
    def resolve_fee(
        self,
        fee_type: FeeType,
        num_passengers: int = 1,
        is_emergency: bool = False,
        channel: BookingChannel = BookingChannel.WHATSAPP,
    ) -> Decimal:
        return self._resolve_fee_op.execute(fee_type, num_passengers, is_emergency, channel)

    def create_snapshot(
        self,
        booking_id: str,
        fee_id: str | None,
        applied_amount: Decimal,
        num_passengers: int,
        channel: BookingChannel,
        emergency: bool,
        actor_id: str,
    ) -> ServiceFeeSnapshotResponse:
        return self._create_snapshot_op.execute(
            booking_id, fee_id, applied_amount, num_passengers, channel, emergency, actor_id
        )
