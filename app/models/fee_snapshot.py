from decimal import Decimal

from sqlalchemy import (
    Boolean, Enum, ForeignKey, Numeric, String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import BookingChannel, FeeType

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from app.models.booking import Booking

class ServiceFeeSnapshot(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "service_fee_snapshots"

    booking_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        doc="One snapshot per booking.",
    )
    fee_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("service_fees.id", ondelete="SET NULL"),
        nullable=True,
        doc="Source fee row (may become NULL if fee is later deleted).",
    )
    fee_type: Mapped[FeeType] = mapped_column(
        Enum(FeeType, name="fee_type_enum_snap"),
        nullable=False,
        doc="Denormalised copy so the type is always queryable.",
    )
    fee_label: Mapped[str] = mapped_column(
        String(200), nullable=False,
        doc="Denormalised label at time of booking.",
    )
    base_amount_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False,
        doc="Per-unit fee before pax multiplication.",
    )
    applied_amount_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False,
        doc="Final fee actually charged (after pax count, discounts).",
    )
    num_passengers: Mapped[int | None] = mapped_column(
        db.Integer, nullable=True,
        doc="Pax count used in the calculation.",
    )
    channel: Mapped[BookingChannel] = mapped_column(
        Enum(BookingChannel, name="booking_channel_enum"),
        nullable=False,
        default=BookingChannel.WHATSAPP,
    )
    emergency_surcharge_applied: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    booking: Mapped["Booking"] = relationship("Booking", back_populates="fee_snapshot")

    def __init__(self, **kwargs: Any) -> None:
        super(ServiceFeeSnapshot, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return (
            f"<ServiceFeeSnapshot booking={self.booking_id} "
            f"${self.applied_amount_usd}>"
        )