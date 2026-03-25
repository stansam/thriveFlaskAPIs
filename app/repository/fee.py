"""Repositories for ServiceFeeSchedule, ServiceFee, ServiceFeeSnapshot."""

from __future__ import annotations

from sqlalchemy import select

from models import ServiceFeeSchedule, ServiceFee, FeeType, ServiceFeeSnapshot
from .base import BaseRepository


class ServiceFeeScheduleRepository(BaseRepository[ServiceFeeSchedule]):
    model = ServiceFeeSchedule

    def find_active(self) -> ServiceFeeSchedule | None:
        stmt = select(ServiceFeeSchedule).where(
            ServiceFeeSchedule.is_active.is_(True)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def deactivate_all(self, actor_id: str | None = None) -> None:
        schedules = self.list_by(is_active=True)
        for s in schedules:
            self.update(s, actor_id=actor_id, is_active=False)


class ServiceFeeRepository(BaseRepository[ServiceFee]):
    model = ServiceFee

    def find_by_schedule(self, schedule_id: str) -> list[ServiceFee]:
        stmt = (
            select(ServiceFee)
            .where(ServiceFee.schedule_id == schedule_id)
            .order_by(ServiceFee.fee_type)
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_active_by_type(self, fee_type: FeeType) -> ServiceFee | None:
        """
        Look up the active fee row for a given type.
        Requires joining through the active schedule.
        """
        stmt = (
            select(ServiceFee)
            .join(ServiceFeeSchedule, ServiceFee.schedule_id == ServiceFeeSchedule.id)
            .where(
                ServiceFeeSchedule.is_active.is_(True),
                ServiceFee.fee_type == fee_type,
                ServiceFee.is_active.is_(True),
            )
        )
        return self._session.execute(stmt).scalar_one_or_none()


class ServiceFeeSnapshotRepository(BaseRepository[ServiceFeeSnapshot]):
    model = ServiceFeeSnapshot

    def find_by_booking(self, booking_id: str) -> ServiceFeeSnapshot | None:
        return self.get_by(booking_id=booking_id)
