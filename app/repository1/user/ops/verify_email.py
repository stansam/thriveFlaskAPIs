from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, timezone
import uuid
from app.models import User
from app.repository.user.ops.get import GetUserByID
from app.repository.user.exceptions import InvalidCredentials, InvalidVerificationToken, EmailAlreadyVerified, UserNotFound, DatabaseError

class GenerateEmailVerificationToken:
    def __init__(self, db:Session) -> None:
        self.db = db

    def execute(self, user_id:str) -> User:
        try:
            get_user_op = GetUserByID(self.db)
            try:
                user = get_user_op.execute(user_id)
            except UserNotFound as e:
                raise UserNotFound("User not found") from e
                        
            user.email_verification_token = str(uuid.uuid4())
            user.email_verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while generating email verification token: {str(e)}") from e

class VerifyUserEmail:
    def __init__(self, db:Session) -> None:
        self.db = db

    def execute(self, user_id:str, token:str) -> User:
        try:
            get_user_op = GetUserByID(self.db)
            try:
                user = get_user_op.execute(user_id)
            except UserNotFound as e:
                raise UserNotFound("User not found") from e

            expires_at = user.email_verification_token_expires_at
            if expires_at and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at < datetime.now(timezone.utc):
                raise InvalidVerificationToken("Verification token expired")
            if user.email_verification_token != token:
                raise InvalidCredentials("Invalid token")
            if user.email_verified:
                raise EmailAlreadyVerified("Email already verified")
            user.email_verified = True
            user.email_verification_token = None
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while verifying email: {str(e)}") from e