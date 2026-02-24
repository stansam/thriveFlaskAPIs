from sqlalchemy.orm import Session
from app.models import Notification
from app.repository.notification.ops import (
    SendNotification,
    MarkAsRead,
    GetUserNotifications
)

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
    
    def send_notification(self, user_id: str, title: str, message: str, notification_type: str, priority: str = "normal") -> Notification:
        return SendNotification(self.db).execute(user_id, title, message, notification_type, priority)

    def mark_as_read(self, notification_id: str) -> Notification:
        return MarkAsRead(self.db).execute(notification_id)

    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> list[Notification]:
        return GetUserNotifications(self.db).execute(user_id, unread_only)
