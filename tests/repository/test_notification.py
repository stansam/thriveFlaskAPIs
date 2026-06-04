import pytest
from datetime import datetime, timedelta, timezone
from app.repository.notification import NotificationRepository, NotificationTemplateRepository
from app.models import Notification, NotificationTemplate
from app.enums import NotificationStatus, NotificationEventType, NotificationChannel, RecipientType, NotificationPriority

@pytest.fixture
def repo():
    return NotificationRepository()

@pytest.fixture
def tmpl_repo():
    return NotificationTemplateRepository()

@pytest.mark.integration
class TestNotificationRepositories:
    def test_template_queries(self, tmpl_repo, db_session):
        t_en = NotificationTemplate(
            event_type=NotificationEventType.BOOKING_CONFIRMED,
            channel=NotificationChannel.EMAIL, language="en", name="en_bk",
            body="English", version=1, is_active=True
        )
        t_es = NotificationTemplate(
            event_type=NotificationEventType.BOOKING_CONFIRMED,
            channel=NotificationChannel.EMAIL, language="es", name="es_bk",
            body="Spanish", version=1, is_active=True
        )
        db_session.add_all([t_en, t_es])
        db_session.flush()

        # exact match
        found = tmpl_repo.find_for_event(NotificationEventType.BOOKING_CONFIRMED, NotificationChannel.EMAIL, "es")
        assert found == t_es

        # fallback to English
        fallback = tmpl_repo.find_for_event(NotificationEventType.BOOKING_CONFIRMED, NotificationChannel.EMAIL, "fr")
        assert fallback == t_en

        all_tmpls = tmpl_repo.find_all_for_event(NotificationEventType.BOOKING_CONFIRMED)
        assert len(all_tmpls) == 2

    def test_notification_pagination_and_read(self, repo, db_session):
        n1 = Notification(
            event_type=NotificationEventType.BOOKING_CONFIRMED,
            recipient_type=RecipientType.CLIENT, recipient_id="C1",
            title="T", body="B", status=NotificationStatus.PENDING,
            priority=NotificationPriority.NORMAL
        )
        n2 = Notification(
            event_type=NotificationEventType.BOOKING_CONFIRMED,
            recipient_type=RecipientType.CLIENT, recipient_id="C1",
            title="T", body="B", status=NotificationStatus.READ,
            priority=NotificationPriority.NORMAL
        )
        db_session.add_all([n1, n2])
        db_session.flush()

        page_all = repo.find_for_recipient(RecipientType.CLIENT, "C1")
        assert len(page_all.items) == 2

        page_unread = repo.find_for_recipient(RecipientType.CLIENT, "C1", unread_only=True)
        assert len(page_unread.items) == 1
        assert page_unread.items[0] == n1

        count = repo.unread_count(RecipientType.CLIENT, "C1")
        assert count == 1

        repo.mark_read(n1)
        db_session.flush()
        db_session.refresh(n1)
        assert n1.status == NotificationStatus.READ
        assert n1.read_at is not None

        # Reset n1 to test bulk mark_read
        n1.status = NotificationStatus.PENDING
        n1.read_at = None
        db_session.flush()

        count_updated = repo.mark_all_read(RecipientType.CLIENT, "C1")
        assert count_updated == 1
        db_session.refresh(n1)
        assert n1.status == NotificationStatus.READ

    def test_scheduled_ready(self, repo, db_session):
        now = datetime.now(timezone.utc)
        n = Notification(
            event_type=NotificationEventType.BOOKING_CONFIRMED,
            recipient_type=RecipientType.CLIENT, recipient_id="C1",
            title="T", body="B", status=NotificationStatus.PENDING,
            priority=NotificationPriority.NORMAL,
            scheduled_for=now - timedelta(hours=1)
        )
        db_session.add(n)
        db_session.flush()

        ready = repo.find_scheduled_ready(as_of=now)
        assert ready == [n]
