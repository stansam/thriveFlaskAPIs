# services/fee_service.py
"""
FeeService — service fee schedule management and fee resolution.

Implements interfaces.md § 9. FeeService.
"""

from __future__ import annotations

from decimal import Decimal

from app.models.base import db
from app.enums import AuditActionType, FeeType, BookingChannel
from app.core.errors.handlers import BadRequestError, NotFoundError
from app.dto import (
    ServiceFeeCreateRequest,
    ServiceFeeResponse,
    ServiceFeeScheduleCreateRequest,
    ServiceFeeScheduleResponse,
    ServiceFeeSnapshotResponse,
)
from app.repository import (
    fee_schedule_repo, fee_repo, fee_snapshot_repo,
)
from app.interface._base import BaseService
from app.core.logging import get_logger

logger = get_logger(__name__)

_EMERGENCY_SURCHARGE = Decimal("25.00")


class FeeService(BaseService):
    # Queries
    def get_active_schedule(self) -> ServiceFeeScheduleResponse:
        schedule = fee_schedule_repo.find_active()
        if not schedule:
            raise NotFoundError("Active fee schedule")
        return ServiceFeeScheduleResponse.model_validate(schedule)

    def list_schedules(self, page: int = 1, per_page: int = 25) -> dict:
        from sqlalchemy import select
        from models.fee import ServiceFeeSchedule
        stmt = select(ServiceFeeSchedule).order_by(ServiceFeeSchedule.effective_from.desc())
        result = fee_schedule_repo.paginate(stmt, page=page, per_page=per_page)
        items = [ServiceFeeScheduleResponse.model_validate(s) for s in result.items]
        return {"items": items, **self._page_meta(result)}
    # Schedule mutations
    def create_schedule(
        self, data: ServiceFeeScheduleCreateRequest, actor_id: str
    ) -> ServiceFeeScheduleResponse:
        schedule = fee_schedule_repo.create(
            actor_id=actor_id,
            name=data.name,
            description=data.description,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            is_active=False,
        )
        for fee_data in data.fees:
            fee_repo.create(
                actor_id=actor_id,
                schedule_id=schedule.id,
                fee_type=fee_data.fee_type,
                label=fee_data.label,
                amount_usd=fee_data.amount_usd,
                min_amount_usd=fee_data.min_amount_usd,
                max_amount_usd=fee_data.max_amount_usd,
                is_per_passenger=fee_data.is_per_passenger,
                is_percentage=fee_data.is_percentage,
                is_active=True,
            )
        self._audit(
            action=AuditActionType.CREATE,
            actor_id=actor_id,
            entity_type="fee_schedule",
            entity_id=schedule.id,
            description=f"Fee schedule '{data.name}' created with {len(data.fees)} fee lines.",
        )
        db.session.commit()
        return ServiceFeeScheduleResponse.model_validate(schedule)

    def activate_schedule(self, schedule_id: str, actor_id: str) -> ServiceFeeScheduleResponse:
        schedule = fee_schedule_repo.get_or_404(schedule_id)
        fee_schedule_repo.deactivate_all(actor_id=actor_id)
        fee_schedule_repo.update(schedule, actor_id=actor_id, is_active=True)
        self._audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="fee_schedule",
            entity_id=schedule_id,
            description=f"Fee schedule '{schedule.name}' activated.",
        )
        db.session.commit()
        return ServiceFeeScheduleResponse.model_validate(schedule)

    def deactivate_schedule(self, schedule_id: str, actor_id: str) -> None:
        schedule = fee_schedule_repo.get_or_404(schedule_id)
        if not schedule.is_active:
            raise BadRequestError("Schedule is already inactive.")
        active_count = fee_schedule_repo.count(
            __import__("sqlalchemy").select(
                __import__("models.fee", fromlist=["ServiceFeeSchedule"]).ServiceFeeSchedule
            ).where(
                __import__("models.fee", fromlist=["ServiceFeeSchedule"]).ServiceFeeSchedule.is_active.is_(True)
            )
        )
        if active_count <= 1:
            raise BadRequestError("Cannot deactivate the only active fee schedule.")
        fee_schedule_repo.update(schedule, actor_id=actor_id, is_active=False)
        self._audit(
            action=AuditActionType.UPDATE, actor_id=actor_id,
            entity_type="fee_schedule", entity_id=schedule_id,
            description=f"Fee schedule '{schedule.name}' deactivated.",
        )
        db.session.commit()

    def add_fee_to_schedule(
        self, schedule_id: str, data: ServiceFeeCreateRequest, actor_id: str
    ) -> ServiceFeeResponse:
        fee_schedule_repo.get_or_404(schedule_id)
        fee = fee_repo.create(
            actor_id=actor_id,
            schedule_id=schedule_id,
            **data.model_dump(),
        )
        db.session.commit()
        return ServiceFeeResponse.model_validate(fee)

    def update_fee(self, fee_id: str, data: dict, actor_id: str) -> ServiceFeeResponse:
        fee = fee_repo.get_or_404(fee_id)
        fee_repo.update(fee, actor_id=actor_id, **{k: v for k, v in data.items() if v is not None})
        db.session.commit()
        return ServiceFeeResponse.model_validate(fee)

    def deactivate_fee(self, fee_id: str, actor_id: str) -> None:
        fee = fee_repo.get_or_404(fee_id)
        fee_repo.update(fee, actor_id=actor_id, is_active=False)
        db.session.commit()
    # Fee resolution — core business logic
    def resolve_fee(
        self,
        fee_type: FeeType,
        num_passengers: int = 1,
        is_emergency: bool = False,
        channel: BookingChannel = BookingChannel.WHATSAPP,
    ) -> Decimal:
        """
        Compute the exact service fee in USD for a given booking.

        Rules
        -----
        1. Look up the active fee row for `fee_type`.
        2. Use `amount_usd` (the base / minimum of the range).
        3. If `is_per_passenger`, multiply by `num_passengers`.
        4. If `is_emergency` and this is a flight booking, add the
           EMERGENCY_SURCHARGE from the schedule (fetched separately).
        5. Return the computed Decimal.
        """
        fee = fee_repo.find_active_by_type(fee_type)
        if not fee:
            raise BadRequestError(
                f"No active fee found for type '{fee_type.value}'. "
                "Ensure a fee schedule is active."
            )

        amount = fee.amount_usd
        if fee.is_per_passenger:
            amount = amount * num_passengers

        if is_emergency:
            surcharge_fee = fee_repo.find_active_by_type(FeeType.EMERGENCY_SURCHARGE)
            if surcharge_fee:
                amount += surcharge_fee.amount_usd

        return amount

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
        """Write the immutable fee snapshot for a booking."""
        fee = fee_repo.get(fee_id) if fee_id else None
        snapshot = fee_snapshot_repo.create(
            actor_id=actor_id,
            booking_id=booking_id,
            fee_id=fee_id,
            fee_type=fee.fee_type if fee else FeeType.DOMESTIC_FLIGHT,
            fee_label=fee.label if fee else "Service Fee",
            base_amount_usd=fee.amount_usd if fee else applied_amount,
            applied_amount_usd=applied_amount,
            num_passengers=num_passengers,
            channel=channel,
            emergency_surcharge_applied=emergency,
        )
        return ServiceFeeSnapshotResponse.model_validate(snapshot)


fee_service = FeeService()