# app/interface/fee/services.py
"""
Fee Service Operations.

Strict CQRS-oriented operations encapsulating all pricing schedules,
fee execution logic, and isolated transactional footprints mapping
event emissions dynamically.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from app.enums import AuditActionType, FeeType, BookingChannel
from app.core.errors.handlers import BadRequestError, NotFoundError
from app.core.events import event_bus
from app.core.events.dataclass.fee import (
    FeeScheduleCreatedEvent,
    FeeScheduleActivatedEvent,
    FeeScheduleDeactivatedEvent,
    ServiceFeeAddedEvent,
    ServiceFeeUpdatedEvent,
    ServiceFeeDeactivatedEvent,
    FeeSnapshotCreatedEvent,
)
from app.dto import (
    ServiceFeeCreateRequest,
    ServiceFeeResponse,
    ServiceFeeScheduleCreateRequest,
    ServiceFeeScheduleResponse,
    ServiceFeeSnapshotResponse,
)
from app.interface._base import BaseService
from app.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

_EMERGENCY_SURCHARGE = Decimal("25.00")


class _FeeOperation(BaseService):
    """
    Base configuration providing native bounds over Fee endpoints.
    Requires injection parameters mapping repositories safely.
    """
    def __init__(
        self,
        fee_schedule_repo: Any,
        fee_repo: Any,
        fee_snapshot_repo: Any,
        audit_service: Any,
        uow: Any,
    ) -> None:
        self._schedules = fee_schedule_repo
        self._fees = fee_repo
        self._snapshots = fee_snapshot_repo
        self._audits = audit_service
        self._uow = uow


class GetActiveScheduleOperation(_FeeOperation):
    def execute(self) -> ServiceFeeScheduleResponse:
        schedule = self._schedules.find_active()
        if not schedule:
            raise NotFoundError("Active fee schedule")
        return ServiceFeeScheduleResponse.model_validate(schedule)


class ListSchedulesOperation(_FeeOperation):
    def execute(self, page: int = 1, per_page: int = 25) -> dict[str, Any]:
        from sqlalchemy import select
        from app.models import ServiceFeeSchedule
        
        stmt = select(ServiceFeeSchedule).order_by(ServiceFeeSchedule.effective_from.desc())
        result = self._schedules.paginate(stmt, page=page, per_page=per_page)
        items = [ServiceFeeScheduleResponse.model_validate(s) for s in result.items]
        return {"items": items, **self._page_meta(result)}


class CreateScheduleOperation(_FeeOperation):
    def execute(
        self, data: ServiceFeeScheduleCreateRequest, actor_id: str
    ) -> ServiceFeeScheduleResponse:
        with self._uow:
            schedule = self._schedules.create(
                actor_id=actor_id,
                name=data.name,
                description=data.description,
                effective_from=data.effective_from,
                effective_to=data.effective_to,
                is_active=False,
            )
            for fee_data in data.fees:
                self._fees.create(
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
            
            self._audits.log(
                action=AuditActionType.CREATE,
                actor_id=actor_id,
                entity_type="fee_schedule",
                entity_id=schedule.id,
                description=f"Fee schedule '{data.name}' created with {len(data.fees)} fee lines.",
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(FeeScheduleCreatedEvent(
            schedule_id=schedule.id,
            name=schedule.name,
        ))
        logger.info("Fee schedule created: %s (id=%s) by actor=%s", schedule.name, schedule.id, actor_id)
        return ServiceFeeScheduleResponse.model_validate(schedule)


class ActivateScheduleOperation(_FeeOperation):
    def execute(self, schedule_id: str, actor_id: str) -> ServiceFeeScheduleResponse:
        with self._uow:
            schedule = self._schedules.get_or_404(schedule_id)
            self._schedules.deactivate_all(actor_id=actor_id)
            self._schedules.update(schedule, actor_id=actor_id, is_active=True)
            
            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="fee_schedule",
                entity_id=schedule_id,
                description=f"Fee schedule '{schedule.name}' activated.",
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(FeeScheduleActivatedEvent(
            schedule_id=schedule.id,
        ))
        logger.info("Fee schedule activated: %s (id=%s) by actor=%s", schedule.name, schedule.id, actor_id)
        return ServiceFeeScheduleResponse.model_validate(schedule)


class DeactivateScheduleOperation(_FeeOperation):
    def execute(self, schedule_id: str, actor_id: str) -> None:
        from sqlalchemy import select
        from app.models import ServiceFeeSchedule
        
        with self._uow:
            schedule = self._schedules.get_or_404(schedule_id)
            if not schedule.is_active:
                raise BadRequestError("Schedule is already inactive.")
                
            active_count = self._schedules.count(
                select(ServiceFeeSchedule).where(ServiceFeeSchedule.is_active.is_(True))
            )
            if active_count <= 1:
                raise BadRequestError("Cannot deactivate the only active fee schedule.")
                
            self._schedules.update(schedule, actor_id=actor_id, is_active=False)
            
            self._audits.log(
                action=AuditActionType.UPDATE, 
                actor_id=actor_id,
                entity_type="fee_schedule", 
                entity_id=schedule_id,
                description=f"Fee schedule '{schedule.name}' deactivated.",
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(FeeScheduleDeactivatedEvent(
            schedule_id=schedule.id,
        ))
        logger.info("Fee schedule deactivated: %s (id=%s) by actor=%s", schedule.name, schedule.id, actor_id)


class AddFeeToScheduleOperation(_FeeOperation):
    def execute(
        self, schedule_id: str, data: ServiceFeeCreateRequest, actor_id: str
    ) -> ServiceFeeResponse:
        with self._uow:
            self._schedules.get_or_404(schedule_id)
            fee = self._fees.create(
                actor_id=actor_id,
                schedule_id=schedule_id,
                **data.model_dump(),
            )
            self._uow.commit()

        event_bus.publish(ServiceFeeAddedEvent(
            schedule_id=schedule_id,
            fee_id=fee.id,
        ))
        logger.info("Service fee added to schedule %s: %s (id=%s) by actor=%s", schedule_id, fee.label, fee.id, actor_id)
        return ServiceFeeResponse.model_validate(fee)


class UpdateFeeOperation(_FeeOperation):
    def execute(self, fee_id: str, data: dict[str, Any], actor_id: str) -> ServiceFeeResponse:
        with self._uow:
            fee = self._fees.get_or_404(fee_id)
            self._fees.update(fee, actor_id=actor_id, **{k: v for k, v in data.items() if v is not None})
            self._uow.commit()

        event_bus.publish(ServiceFeeUpdatedEvent(
            fee_id=fee.id,
        ))
        logger.info("Service fee updated: %s (id=%s) by actor=%s", fee.label, fee.id, actor_id)
        return ServiceFeeResponse.model_validate(fee)


class DeactivateFeeOperation(_FeeOperation):
    def execute(self, fee_id: str, actor_id: str) -> None:
        with self._uow:
            fee = self._fees.get_or_404(fee_id)
            self._fees.update(fee, actor_id=actor_id, is_active=False)
            self._uow.commit()

        event_bus.publish(ServiceFeeDeactivatedEvent(
            fee_id=fee.id,
        ))


class ResolveFeeOperation(_FeeOperation):
    def execute(
        self,
        fee_type: FeeType,
        num_passengers: int = 1,
        is_emergency: bool = False,
        channel: BookingChannel = BookingChannel.WHATSAPP,
    ) -> Decimal:
        fee = self._fees.find_active_by_type(fee_type)
        if not fee:
            raise BadRequestError(
                f"No active fee found for type '{fee_type.value}'. "
                "Ensure a fee schedule is active."
            )

        amount = fee.amount_usd
        if fee.is_per_passenger:
            amount = amount * num_passengers

        if is_emergency:
            surcharge_fee = self._fees.find_active_by_type(FeeType.EMERGENCY_SURCHARGE)
            if surcharge_fee:
                amount += surcharge_fee.amount_usd

        return amount


class CreateSnapshotOperation(_FeeOperation):
    def execute(
        self,
        booking_id: str,
        fee_id: str | None,
        applied_amount: Decimal,
        num_passengers: int,
        channel: BookingChannel,
        emergency: bool,
        actor_id: str,
    ) -> ServiceFeeSnapshotResponse:
        with self._uow:
            fee = self._fees.get(fee_id) if fee_id else None
            snapshot = self._snapshots.create(
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
            self._uow.commit()

        event_bus.publish(FeeSnapshotCreatedEvent(
            booking_id=booking_id,
            fee_id=snapshot.id,
        ))
        return ServiceFeeSnapshotResponse.model_validate(snapshot)
