# models/notification.py
"""
Notification system — three-layer architecture.

Layer 1: NotificationTemplate
  Reusable, versioned message templates stored by event type.
  Supports variable interpolation via Jinja2-style {{placeholders}}.
  One template per (event_type, channel, language) combination.

Layer 2: Notification
  A concrete notification targeted at one recipient (User or Client).
  Created by the notification service when an event fires.
  Tracks read/unread state for the in-app notification centre.

Layer 3: NotificationDelivery
  One row per delivery attempt on a specific channel (email,
  WhatsApp, SMS, in-app).  Stores provider response, delivery
  status, and retry metadata.

Design decisions
----------------
- Recipient is polymorphic (User OR Client) via `recipient_type` +
  `recipient_id` to avoid two separate notification tables.
- Templates are versioned: `is_active=False` retires a template
  without losing delivery history that references it.
- `NotificationDelivery` is a separate table (not columns on
  Notification) because one notification can be delivered on multiple
  channels simultaneously (e.g. email + WhatsApp for a booking
  confirmation) and each channel has independent retry state.
- `metadata_json` on Notification stores the interpolation context
  at creation time so the template can be re-rendered for debugging
  without reconstructing the original event payload.
"""

from sqlalchemy import (DateTime, 
    Enum, ForeignKey, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import(
    NotificationEventType,
    NotificationPriority,
    NotificationStatus,
    RecipientType,
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.notification_template import NotificationTemplate
    from app.models.notification_delivery import NotificationDelivery

class Notification(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "notifications"

    # Template reference
    template_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("notification_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Source template. NULL for ad-hoc notifications.",
    )
    event_type: Mapped[NotificationEventType] = mapped_column(
        Enum(NotificationEventType, name="notification_event_type_enum_notif"),
        nullable=False,
        index=True,
        doc="Denormalised from template for direct querying.",
    )

    # Recipient (polymorphic)
    recipient_type: Mapped[RecipientType] = mapped_column(
        Enum(RecipientType, name="recipient_type_enum"),
        nullable=False,
        index=True,
    )
    recipient_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True,
        doc="PK of the User or Client receiving this notification.",
    )

    # Content (rendered at creation time)
    title: Mapped[str] = mapped_column(
        String(300), nullable=False,
        doc="Short rendered title for the notification centre card.",
    )
    body: Mapped[str] = mapped_column(
        Text, nullable=False,
        doc="Full rendered message body.",
    )
    context_json: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        doc="JSON of the Jinja2 rendering context at creation time.",
    )

    # Entity reference (for deep-linking)
    entity_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        doc='E.g. "booking", "payment", "package".',
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True,
        doc="PK of the related entity for deep-link navigation.",
    )

    # State
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status_enum"),
        nullable=False,
        default=NotificationStatus.PENDING,
        index=True,
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority, name="notification_priority_enum"),
        nullable=False,
        default=NotificationPriority.NORMAL,
    )
    read_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        doc="Timestamp when the recipient read/opened the notification.",
    )
    dismissed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    scheduled_for: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        doc="Future delivery time for scheduled notifications (e.g. pre-trip reminders).",
    )

    # Relationships
    template: Mapped["NotificationTemplate | None"] = relationship(
        "NotificationTemplate", back_populates="notifications",
    )
    deliveries: Mapped[list["NotificationDelivery"]] = relationship(
        "NotificationDelivery",
        back_populates="notification",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Notification {self.event_type.value} "
            f"→ {self.recipient_type.value}/{self.recipient_id} "
            f"[{self.status.value}]>"
        )

