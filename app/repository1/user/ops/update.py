from app.models import User
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.user.ops.get import GetUserByID
from app.repository.user.exceptions import UserNotFound, DatabaseError

class UpdateUser:
    def __init__(self, db:Session) -> None:
        self.db = db

    def execute(self, user_id:str, user_data:dict) -> User:
        try:
            get_user_op = GetUserByID(self.db)
            try:
                user = get_user_op.execute(user_id)
            except UserNotFound as e:
                raise UserNotFound("User not found") from e

            for key, value in user_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user

        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while updating user: {str(e)}") from e