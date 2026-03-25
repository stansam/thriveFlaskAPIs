# models/referral.py
"""
Referral tracking.

When client A refers client B, a Referral row is created.
On B's first completed booking the status transitions to QUALIFIED → CREDITED,
and a LoyaltyLedger row is written granting A a $10 credit.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import AuditMixin, db
from app.enums import ReferralStatus

if TYPE_CHECKING:
    pass

class Referral(db.Model, AuditMixin):
    """
    One referral event linking two Client records.

    referrer_id           — the client who made the referral
    referee_id            — the client who was referred
    credit_usd            — credit to award on qualification (default $10)
    qualifying_booking_id — the booking that triggered QUALIFIED
    """

    __tablename__ = "referrals"

    referrer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ReferralStatus] = mapped_column(
        Enum(ReferralStatus, name="referral_status_enum"),
        nullable=False,
        default=ReferralStatus.PENDING,
        index=True,
    )
    credit_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("10.00"),
        doc="Credit awarded to referrer on qualification.",
    )
    qualifying_booking_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        doc="The booking that caused PENDING → QUALIFIED.",
    )

    def __repr__(self) -> str:
        return (
            f"<Referral {self.referrer_id}→{self.referee_id} "
            f"[{self.status.value}]>"
        )
