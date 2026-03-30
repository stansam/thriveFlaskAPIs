from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import FeeType

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.fee_schedule import ServiceFeeSchedule

class ServiceFee(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "service_fees"

    schedule_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("service_fee_schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fee_type: Mapped[FeeType] = mapped_column(
        Enum(FeeType, name="fee_type_enum"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(
        String(200), nullable=False,
        doc='Human-readable name, e.g. "International Flight Booking Fee".',
    )
    amount_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False,
        doc="Base fee amount (or minimum if a range applies).",
    )
    min_amount_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True,
        doc="Lower bound of fee range. NULL if fixed.",
    )
    max_amount_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True,
        doc="Upper bound of fee range. NULL if fixed.",
    )
    is_per_passenger: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="Multiply fee by passenger count if True.",
    )
    is_percentage: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="fee = amount_usd% of ticket cost if True.",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    schedule: Mapped["ServiceFeeSchedule"] = relationship(
        "ServiceFeeSchedule", back_populates="fees"
    )

    def __repr__(self) -> str:
        return f"<ServiceFee {self.fee_type.value} ${self.amount_usd}>"
