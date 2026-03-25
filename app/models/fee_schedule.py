from sqlalchemy import (
    Boolean, Date, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, db

class ServiceFeeSchedule(db.Model, AuditMixin):
    """
    A named, versioned container for a set of service fees.

    Only one schedule should be `is_active=True` at a time.
    Deactivating a schedule does not affect existing bookings because
    those are anchored to `ServiceFeeSnapshot`.

    Example:
      name = "Standard 2024 Q1"
      effective_from = 2024-01-01
      is_active = True
    """

    __tablename__ = "service_fee_schedules"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_from: Mapped[db.Date] = mapped_column(db.Date, nullable=False)
    effective_to: Mapped[db.Date | None] = mapped_column(db.Date, nullable=True)
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
