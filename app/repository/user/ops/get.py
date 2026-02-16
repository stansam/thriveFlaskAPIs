from app.models import User
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.user.exceptions import UserNotFound, DatabaseError
class GetUserByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_id: str) -> User:
        try:
            user = self.db.query(User).filter_by(id=user_id).first()
            if not user:
                raise UserNotFound("User not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user: {str(e)}") from e
        
class GetUsers:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[User]:
        try:
            users = self.db.query(User).all()
            if not users:
                raise UserNotFound("Users not found")
            return users
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching users: {str(e)}") from e
