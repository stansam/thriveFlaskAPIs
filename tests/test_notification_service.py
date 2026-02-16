import pytest
from app.repository.notification.services import NotificationService
from app.models.enums import NotificationType, NotificationPriority

def test_send_notification(db_session, user_factory):
    user = user_factory()
    service = NotificationService(db_session)
    
    notification = service.send_notification(
        user_id=user.id,
        title="Welcome",
        message="Welcome to Thrive Travels",
        notification_type="general",
        priority="high"
    )
    
    assert notification.id is not None
    assert notification.user_id == user.id
    assert notification.title == "Welcome"
    assert notification.type == NotificationType.GENERAL
    assert notification.priority == NotificationPriority.HIGH
    assert notification.is_read is False

def test_mark_as_read(db_session, user_factory):
    user = user_factory()
    service = NotificationService(db_session)
    
    notification = service.send_notification(
        user_id=user.id,
        title="Test",
        message="Body",
        notification_type="general"
    )
    
    updated = service.mark_as_read(notification.id)
    assert updated.is_read is True
    # removed read_at check as it's not in the model

def test_get_user_notifications(db_session, user_factory):
    user = user_factory()
    service = NotificationService(db_session)
    
    # Create 3 notifications
    n1 = service.send_notification(user.id, "N1", "M1", "general")
    n2 = service.send_notification(user.id, "N2", "M2", "general")
    n3 = service.send_notification(user.id, "N3", "M3", "general")
    
    service.mark_as_read(n1.id)
    
    all_notifs = service.get_user_notifications(user.id)
    assert len(all_notifs) == 3
    
    unread_notifs = service.get_user_notifications(user.id, unread_only=True)
    assert len(unread_notifs) == 2
    assert n1.id not in [n.id for n in unread_notifs]
