from decimal import Decimal
from typing import TYPE_CHECKING, Any
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import LoyaltyTransactionType

if TYPE_CHECKING:
    from app.models.client import Client

class LoyaltyLedger(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "loyalty_ledger"

    client_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[LoyaltyTransactionType] = mapped_column(
        Enum(LoyaltyTransactionType, name="loyalty_tx_type_enum"),
        nullable=False,
        index=True,
    )
    amount_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        doc="Signed amount. Positive = earned, negative = redeemed/expired.",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable explanation shown in the client portal.",
    )
    # Optional links for context
    booking_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Booking this transaction is related to.",
    )
    referral_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("referrals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Referral that generated this credit.",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When this credit expires. NULL = does not expire.",
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="loyalty_entries",
        foreign_keys=[client_id],
    )

    def __init__(self, **kwargs: Any) -> None:
        super(LoyaltyLedger, self).__init__(**kwargs)

    def __repr__(self) -> str:
        sign = "+" if self.amount_usd >= 0 else ""
        return (
            f"<LoyaltyLedger client={self.client_id} "
            f"{sign}{self.amount_usd} [{self.transaction_type.value}]>"
        )
