import pytest
from app.models.notification_template import NotificationTemplate
from app.enums import NotificationEventType, NotificationChannel

def test_notification_template_creation(db_session):
    """Test NotificationTemplate model creation."""
    template = NotificationTemplate(
        event_type=NotificationEventType.BOOKING_CONFIRMED,
        channel=NotificationChannel.EMAIL,
        language="en",
        name="Booking Confirmed EN",
        subject="Confirmed!",
        body="Hello {{ name }}, your booking is confirmed."
    )
    db_session.add(template)
    db_session.commit()

    assert template.id is not None
    assert template.event_type == NotificationEventType.BOOKING_CONFIRMED
    assert template.version == 1
    assert template.is_active is True
