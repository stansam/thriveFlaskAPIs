from sqlalchemy.orm import Session
from app.models import User
from app.repository.user.exceptions import UserNotFound, DatabaseError
from sqlalchemy.exc import SQLAlchemyError

class DeleteUser:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_id: str) -> User:
        try:
            user = self.db.query(User).filter_by(id=user_id).first()
            if not user:
                raise UserNotFound("User not found")
            user.soft_delete()
            # self.db.commit()
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while deleting user: {str(e)}") from e
        