from sqlalchemy import (Date, 
    Boolean, Date, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.fee import ServiceFee

class ServiceFeeSchedule(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "service_fee_schedules"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_from: Mapped[Date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="Only one schedule should be active at a time.",
    )

    fees: Mapped[list["ServiceFee"]] = relationship(
        "ServiceFee",
        back_populates="schedule",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ServiceFeeSchedule {self.name!r} active={self.is_active}>"
