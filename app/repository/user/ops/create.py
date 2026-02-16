from app.models import User
from app.extensions import db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.repository.user.exceptions import UserAlreadyExists, DatabaseError

class CreateUser:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_data: dict) -> User:
        try:
            password = user_data.pop('password', None)
            
            new_user = User(**user_data)
            
            if password:
                new_user.set_password(password)
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            return new_user
        except IntegrityError as e:
            self.db.rollback()
            raise UserAlreadyExists("User already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError("Database error while creating user") from e