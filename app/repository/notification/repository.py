from typing import List, Optional
from app.extensions import db
from app.models.notification import Notification, NotificationTemplate
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions

class NotificationRepository(BaseRepository[Notification]):
    """
    NotificationRepository managing the delivery state of messages sent
    to users and bulk state mutations.
    """

    def __init__(self):
        super().__init__(Notification)

    @handle_db_exceptions
    def get_unread_notifications(self, user_id: str, limit: int = 20) -> List[Notification]:
        """Fetches unread messages ordered securely by creation date descendant."""
        return self.model.query.filter_by(
            user_id=user_id,
            is_read=False
        ).order_by(self.model.created_at.desc()).limit(limit).all()

    @handle_db_exceptions
    def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        """Flips the boolean `is_read` flag safely for an isolated alert."""
        notification = self.get_by_id(notification_id)
        if not notification:
            return None
            
        notification.is_read = True
        db.session.commit()
        return notification

    @handle_db_exceptions
    def mark_all_as_read_for_user(self, user_id: str) -> bool:
        """
        Performs a bulk update flipping the read state for all lingering
        unread entries belonging to a given user.
        """
        self.model.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({"is_read": True}, synchronize_session=False)
        db.session.commit()
        return True

    @handle_db_exceptions
    def get_notification_template(self, trigger_event: str) -> Optional[NotificationTemplate]:
        """Fetches the dynamically configurable HTML/Text payload maps tied to explicit platform events."""
        return NotificationTemplate.query.filter_by(
            trigger_event=trigger_event,
            is_active=True
        ).first()
