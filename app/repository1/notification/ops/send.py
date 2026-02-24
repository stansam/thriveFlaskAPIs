from app.models import Notification
from app.models.enums import NotificationPriority, NotificationType
from app.extensions import db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.notification.exceptions import DatabaseError
import uuid

class SendNotification:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_id: str, title: str, message: str, notification_type: str, priority: str = "normal") -> Notification:
        try:
            try:
                type_enum = NotificationType(notification_type)
            except ValueError:
                 type_enum = NotificationType.GENERAL

            try:
                priority_enum = NotificationPriority(priority)
            except ValueError:
                 priority_enum = NotificationPriority.NORMAL

            new_notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=type_enum,
                priority=priority_enum
            )
            
            self.db.add(new_notification)
            self.db.commit()
            self.db.refresh(new_notification)
            return new_notification

        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while creating notification: {str(e)}") from e
