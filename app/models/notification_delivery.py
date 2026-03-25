from sqlalchemy import (
    Enum, ForeignKey, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, db
from app.enums import(
    NotificationChannel,
    DeliveryStatus,
)

class NotificationDelivery(db.Model, AuditMixin):
    """
    One delivery attempt on a specific channel for a Notification.

    A single Notification can have multiple Delivery rows:
      - One per channel (email, WhatsApp, in-app simultaneously)
      - Additional rows for retries on failure

    `provider_message_id` stores the external ID returned by the
    delivery provider (SendGrid message ID, Twilio SID, etc.) for
    reconciliation and webhook lookups.

    `provider_response_json` captures the raw API response body for
    debugging without requiring a separate log query.

    Retry logic:
      `attempt_number` increments on each retry.
      `next_retry_at`  is set by the retry scheduler.
      Max retries enforced at the application layer (typically 3).
    """

    __tablename__ = "notification_deliveries"

    notification_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel_enum_del"),
        nullable=False,
        index=True,
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status_enum"),
        nullable=False,
        default=DeliveryStatus.QUEUED,
        index=True,
    )

    # Addressing
    recipient_address: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        doc="Email address / phone number / WhatsApp number used for delivery.",
    )

    # Provider tracking
    provider_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        doc='E.g. "sendgrid", "twilio", "wati", "internal".',
    )
    provider_message_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        doc="External message ID from the delivery provider.",
    )
    provider_response_json: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        doc="Raw JSON response body from the provider API call.",
    )

    # Retry metadata
    attempt_number: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1,
        doc="1-indexed attempt counter.",
    )
    sent_at: Mapped[db.DateTime | None] = mapped_column(
        db.DateTime(timezone=True), nullable=True,
        doc="When the delivery request was dispatched to the provider.",
    )
    delivered_at: Mapped[db.DateTime | None] = mapped_column(
        db.DateTime(timezone=True), nullable=True,
        doc="Confirmed delivery timestamp (from provider webhook).",
    )
    opened_at: Mapped[db.DateTime | None] = mapped_column(
        db.DateTime(timezone=True), nullable=True,
        doc="Email open / WhatsApp read-receipt timestamp.",
    )
    failed_at: Mapped[db.DateTime | None] = mapped_column(
        db.DateTime(timezone=True), nullable=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        doc="Human-readable failure description for admin display.",
    )
    next_retry_at: Mapped[db.DateTime | None] = mapped_column(
        db.DateTime(timezone=True), nullable=True,
        doc="Scheduled time for the next retry attempt.",
    )

    # Relationship
    notification: Mapped["Notification"] = relationship(
        "Notification", back_populates="deliveries",
    )

    def __repr__(self) -> str:
        return (
            f"<NotificationDelivery notif={self.notification_id} "
            f"[{self.channel.value}/{self.status.value}] "
            f"attempt={self.attempt_number}>"
        )
