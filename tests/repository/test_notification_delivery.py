import pytest
from datetime import datetime, timedelta
from app.repository.notification_delivery import NotificationDeliveryRepository
from app.models import NotificationDelivery, Notification
from app.enums import NotificationChannel, DeliveryStatus, NotificationEventType, RecipientType, NotificationPriority, NotificationStatus

@pytest.fixture
def repo():
    return NotificationDeliveryRepository()

@pytest.mark.integration
class TestNotificationDeliveryRepository:
    def test_queries(self, repo, db_session):
        n = Notification(
            event_type=NotificationEventType.BOOKING_CONFIRMED,
            recipient_type=RecipientType.CLIENT, recipient_id="C1",
            title="T", body="B", status=NotificationStatus.PENDING,
            priority=NotificationPriority.NORMAL
        )
        db_session.add(n)
        db_session.flush()

        now = datetime.utcnow()
        d1 = NotificationDelivery(
            notification_id=str(n.id), channel=NotificationChannel.EMAIL,
            status=DeliveryStatus.SENT, recipient_address="a@a.com",
            provider_name="sendgrid", provider_message_id="msg1"
        )
        d2 = NotificationDelivery(
            notification_id=str(n.id), channel=NotificationChannel.WHATSAPP,
            status=DeliveryStatus.RETRYING, recipient_address="123",
            provider_name="twilio", next_retry_at=now - timedelta(minutes=10)
        )
        db_session.add_all([d1, d2])
        db_session.flush()

        deliveries = repo.find_by_notification(str(n.id))
        assert len(deliveries) == 2

        retryable = repo.find_retryable(as_of=now)
        assert len(retryable) == 1
        assert retryable[0] == d2

        by_msg_id = repo.find_by_provider_message_id("msg1")
        assert by_msg_id == d1
        
        assert repo.find_by_provider_message_id("missing") is None
