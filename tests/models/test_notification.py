import pytest
from app.models.notification import Notification
from app.enums import NotificationEventType, NotificationPriority, NotificationStatus, RecipientType

def test_notification_creation(db_session):
    """Test Notification model creation and polymorphic recipient."""
    notification = Notification(
        event_type=NotificationEventType.BOOKING_CONFIRMED,
        recipient_type=RecipientType.CLIENT,
        recipient_id="client-123",
        title="Booking Confirmed",
        body="Your booking TG-123 has been confirmed.",
        status=NotificationStatus.PENDING,
        priority=NotificationPriority.NORMAL
    )
    db_session.add(notification)
    db_session.flush()

    assert notification.id is not None
    assert notification.event_type == NotificationEventType.BOOKING_CONFIRMED
    assert notification.recipient_type == RecipientType.CLIENT
    assert notification.read_at is None
