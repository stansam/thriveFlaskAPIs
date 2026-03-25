# models/fee.py
"""
Service fee pricing models.

The business plan specifies a detailed fee matrix:
  Domestic flights            $25–$50
  International flights       $50–$100
  Emergency surcharge         +$25
  Group bookings              $15/pax (min 5)
  Hotel booking               $20 flat
  Car rental booking          $15 flat
  Itinerary (custom)          $50–$150

  Corporate plans:
    Bronze                    $150/month / 6 bookings
    Silver                    $300/month / 15 bookings
    Gold                      $500/month / unlimited + 24/7

Rather than hardcoding these values, we store them in a versioned
`ServiceFeeSchedule` that contains `ServiceFee` rows.  This means:

1. The admin can update fees via the API without a code deploy.
2. History is preserved — we can always audit what fee applied
   to an old booking.
3. At booking creation time, a `ServiceFeeSnapshot` is written to
   lock in the fee row that was in effect, so future schedule changes
   don't retroactively alter existing bookings.

Usage
-----
On booking creation:
  1. Look up the applicable ServiceFee (by FeeType + flags).
  2. Compute total_service_fee_usd (fee.amount or fee.amount × pax).
  3. Write a ServiceFeeSnapshot linked to the booking.
"""

from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, db
from app.enums import FeeType

class ServiceFee(db.Model, AuditMixin):
    """
    A single fee line within a ServiceFeeSchedule.

    `amount_usd` is the base fee value.
    `is_per_passenger` controls whether the fee multiplies by pax count.
    `is_percentage` signals the fee is a % of the ticket/package price
      (used for insurance commissions).
    `min_amount_usd` / `max_amount_usd` define the allowable range for
      fees that have a band (e.g. domestic $25–$50).  The booking service
      can choose any value in this range; the selected value is snapshotted.
    """

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
