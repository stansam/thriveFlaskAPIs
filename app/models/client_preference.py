from sqlalchemy import (
    Boolean, Enum, ForeignKey, Integer, String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING
from app.models.base import AuditMixin, db

if TYPE_CHECKING:
    from app.models.client import Client
from app.enums import PreferredChannel, DocumentFormat

# ClientPreference  (1:1 with Client)
class ClientPreference(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "client_preferences"

    client_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Communication
    preferred_channel: Mapped[PreferredChannel] = mapped_column(
        Enum(PreferredChannel, name="preferred_channel_enum"),
        nullable=False,
        default=PreferredChannel.WHATSAPP,
    )
    preferred_document_format: Mapped[DocumentFormat] = mapped_column(
        Enum(DocumentFormat, name="document_format_enum"),
        nullable=False,
        default=DocumentFormat.PDF,
    )

    # Opt-ins
    marketing_opt_in: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        doc="Client consents to receive marketing messages and flight deals.",
    )
    booking_reminders: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        doc="Send pre-travel reminder notifications.",
    )
    travel_reminder_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, default=48,
        doc="Hours before departure to send travel reminder.",
    )
    payment_reminders: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        doc="Send reminder when a booking has an outstanding balance.",
    )

    # Display
    language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en",
        doc="BCP-47 language tag for client-facing communications.",
    )
    preferred_currency_display: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD",
        doc="Display currency for the client portal (ISO 4217). Amounts stored in USD.",
    )
    timezone: Mapped[str] = mapped_column(
        String(60), nullable=False, default="UTC",
        doc="IANA timezone for scheduling reminder delivery times.",
    )

    # Relationship
    client: Mapped["Client"] = relationship(
        "Client", back_populates="preference", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<ClientPreference client={self.client_id} "
            f"channel={self.preferred_channel.value}>"
        )
