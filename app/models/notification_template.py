
from sqlalchemy import (
    Boolean, Enum, Integer, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING
from app.models.base import AuditMixin, db

if TYPE_CHECKING:
    from app.models.notification import Notification
from app.enums import NotificationEventType, NotificationChannel

class NotificationTemplate(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "notification_templates"

    event_type: Mapped[NotificationEventType] = mapped_column(
        Enum(NotificationEventType, name="notification_event_type_enum"),
        nullable=False,
        index=True,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel_enum"),
        nullable=False,
        index=True,
    )
    language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en",
        doc="BCP-47 language tag, e.g. 'en', 'sw' (Swahili), 'fr'.",
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        doc='Human-readable template name, e.g. "Booking Confirmed — Email EN".',
    )
    subject: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        doc="Email subject line. NULL for non-email channels.",
    )
    body: Mapped[str] = mapped_column(
        Text, nullable=False,
        doc="Message body with Jinja2 {{ variable }} placeholders.",
    )
    variable_schema: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        doc="JSON Schema string documenting available template variables.",
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        doc="Incremented on each content edit for delivery audit trail.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="template",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return (
            f"<NotificationTemplate {self.event_type.value} "
            f"[{self.channel.value}/{self.language}] v{self.version}>"
        )
