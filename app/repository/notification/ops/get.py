from app.models import Notification
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.notification.exceptions import DatabaseError

class GetUserNotifications:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_id: str, unread_only: bool = False) -> list[Notification]:
        try:
            query = self.db.query(Notification).filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            return query.order_by(Notification.created_at.desc()).all()
            
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching notifications: {str(e)}") from e
