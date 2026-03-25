# models/loyalty.py
"""
Loyalty credit ledger.

Uses a double-entry-style append-only approach:
  - Positive rows  = credits earned  (referral, booking reward)
  - Negative rows  = credits redeemed (applied to a booking fee)

Running balance = SELECT SUM(amount_usd) FROM loyalty_ledger WHERE client_id = ?

This avoids a mutable "balance" column that can drift out of sync.
A database view or service-layer method computes the current balance
on demand.

Background jobs should create EXPIRY rows when credit_usd would
otherwise sit unused past its `expires_at` date.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, db
from app.enums import LoyaltyTransactionType

if TYPE_CHECKING:
    from .client import Client

class LoyaltyLedger(db.Model, AuditMixin):
    """
    One line-item in the loyalty ledger for a Client.

    `amount_usd` is signed:
        > 0   credit earned / granted
        < 0   credit redeemed / expired

    `expires_at` is set on newly issued credits.  NULL on redemptions
    and expiry rows.
    """

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
    expires_at: Mapped[db.DateTime | None] = mapped_column(
        db.DateTime(timezone=True),
        nullable=True,
        doc="When this credit expires. NULL = does not expire.",
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="loyalty_entries",
        foreign_keys=[client_id],
    )

    def __repr__(self) -> str:
        sign = "+" if self.amount_usd >= 0 else ""
        return (
            f"<LoyaltyLedger client={self.client_id} "
            f"{sign}{self.amount_usd} [{self.transaction_type.value}]>"
        )
