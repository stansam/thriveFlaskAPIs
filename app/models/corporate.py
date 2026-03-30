from decimal import Decimal

from sqlalchemy import (DateTime, 
    Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING
from app.models.base import AuditMixin, db

if TYPE_CHECKING:
    from app.models.client import Client
from app.enums import SubscriptionTier

class CorporateAccount(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "corporate_accounts"

    company_name: Mapped[str] = mapped_column(String(300), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    billing_email: Mapped[str] = mapped_column(String(254), nullable=False)
    billing_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="EIN / VAT / local tax identifier.",
    )
    primary_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    primary_contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # One-to-one active subscription (nullable — account may lapse)
    subscription: Mapped["CorporateSubscription | None"] = relationship(
        "CorporateSubscription",
        back_populates="account",
        uselist=False,
        lazy="joined",
    )
    clients: Mapped[list["Client"]] = relationship(
        "Client",
        back_populates="corporate_account",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<CorporateAccount {self.company_name}>"


class CorporateSubscription(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    """
    The active pricing plan for a CorporateAccount.

    `bookings_used` is incremented by the booking service each time a
    booking is completed under this account.  It is reset to 0 on each
    billing cycle renewal.

    `bookings_limit` is NULL for GOLD (unlimited) plans.
    `concierge_247`  flags whether 24/7 support is included.
    """

    __tablename__ = "corporate_subscriptions"

    account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("corporate_accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,          # only one subscription per account
        index=True,
    )
    tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier, name="subscription_tier_enum"),
        nullable=False,
    )
    monthly_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        doc="Contracted monthly fee in USD.",
    )
    bookings_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Max bookings per billing cycle. NULL = unlimited (Gold).",
    )
    bookings_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Bookings consumed in the current billing cycle.",
    )
    concierge_247: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether 24/7 concierge support is included.",
    )
    billing_cycle_start: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    billing_cycle_end: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    account: Mapped["CorporateAccount"] = relationship(
        "CorporateAccount",
        back_populates="subscription",
    )

    def is_at_limit(self) -> bool:
        """Returns True if this subscription has hit its monthly cap."""
        if self.bookings_limit is None:
            return False
        return self.bookings_used >= self.bookings_limit

    def __repr__(self) -> str:
        return f"<CorporateSubscription {self.tier.value} — {self.account_id}>"

