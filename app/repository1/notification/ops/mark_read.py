from app.models import Notification
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.notification.exceptions import NotificationNotFound, DatabaseError

class MarkAsRead:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, notification_id: str) -> Notification:
        try:
            notification = self.db.query(Notification).filter_by(id=notification_id).first()
            if not notification:
                raise NotificationNotFound(f"Notification with ID {notification_id} not found")
            
            if not notification.is_read:
                notification.is_read = True
                self.db.commit()
                self.db.refresh(notification)
            
            return notification
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while marking notification as read: {str(e)}") from e
