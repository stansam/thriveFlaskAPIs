from typing import TYPE_CHECKING, Any

from sqlalchemy import (Date, 
    Boolean, Enum, ForeignKey, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import ClientType

if TYPE_CHECKING:
    from app.models.corporate import CorporateAccount
    from app.models.booking import Booking
    from app.models.loyalty import LoyaltyLedger
    from app.models.client_preference import ClientPreference


class Client(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "clients"

    # Personal info
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(254), unique=True, nullable=False, index=True
    )
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    whatsapp_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        doc="May differ from phone; used for WhatsApp broadcast lists.",
    )
    nationality: Mapped[str | None] = mapped_column(
        String(100), nullable=True, doc="Country of citizenship."
    )
    passport_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Stored encrypted at application layer. Used for flight bookings.",
    )
    passport_expiry: Mapped[Date | None] = mapped_column(
        Date, nullable=True
    )
    date_of_birth: Mapped[Date | None] = mapped_column(
        Date, nullable=True, doc="Required for international itineraries."
    )
    preferred_language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en"
    )

    # Classification
    client_type: Mapped[ClientType] = mapped_column(
        Enum(ClientType, name="client_type_enum"),
        nullable=False,
        default=ClientType.INDIVIDUAL,
    )
    is_group_leader: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Internal CRM notes (not shown to client)."
    )

    # Corporate association (nullable for non-corporate clients)
    corporate_account_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("corporate_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Referral self-FK
    referred_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    corporate_account: Mapped["CorporateAccount | None"] = relationship(
        "CorporateAccount",
        back_populates="clients",
    )
    referrer: Mapped["Client | None"] = relationship(
        "Client",
        remote_side="Client.id",
        foreign_keys=[referred_by_id],
        back_populates="referrals_made",
    )
    referrals_made: Mapped[list["Client"]] = relationship(
        "Client",
        foreign_keys=[referred_by_id],
        back_populates="referrer",
        lazy="dynamic",
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="client",
        lazy="dynamic",
    )
    loyalty_entries: Mapped[list["LoyaltyLedger"]] = relationship(
        "LoyaltyLedger",
        back_populates="client",
        lazy="dynamic",
    )
    preference: Mapped["ClientPreference | None"] = relationship(
        "ClientPreference",
        back_populates="client",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __init__(self, **kwargs: Any) -> None:
        super(Client, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Client {self.full_name} [{self.client_type.value}]>"
