import pytest
from app.models.notification_delivery import NotificationDelivery
from app.models.notification import Notification
from app.enums import NotificationChannel, DeliveryStatus, NotificationEventType, RecipientType

def test_notification_delivery_creation(db_session):
    """Test NotificationDelivery model and its link to Notification."""
    notification = Notification(
        event_type=NotificationEventType.BOOKING_CONFIRMED,
        recipient_type=RecipientType.CLIENT,
        recipient_id="client-123",
        title="Test",
        body="Test Body"
    )
    db_session.add(notification)
    db_session.flush()

    delivery = NotificationDelivery(
        notification_id=notification.id,
        channel=NotificationChannel.EMAIL,
        status=DeliveryStatus.SENT,
        recipient_address="test@example.com",
        provider_name="sendgrid"
    )
    db_session.add(delivery)
    db_session.flush()

    assert delivery.id is not None
    assert delivery.notification.event_type == NotificationEventType.BOOKING_CONFIRMED
    assert delivery.channel == NotificationChannel.EMAIL
