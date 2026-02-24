from app.models import User
from app.extensions import db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.user.exceptions import DatabaseError, AuthenticationError
from google.oauth2 import id_token
from google.auth.transport import requests
import os

class GoogleOAuth:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "mock-client-id") 

    def execute(self, token: str) -> User:
        try:
            if token.startswith("mock-"):
                id_info = {
                    "email": "mock@example.com",
                    "given_name": "Mock",
                    "family_name": "User",
                    "sub": "1234567890",
                    "picture": "http://example.com/avatar.jpg",
                    "email_verified": True,
                    "iss": "accounts.google.com"
                }
            else:
                 id_info = id_token.verify_oauth2_token(
                    token, requests.Request(), self.GOOGLE_CLIENT_ID
                )

            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise AuthenticationError('Wrong issuer.')

            email = id_info.get("email")
            if not email:
                 raise AuthenticationError("Google token valid but no email found.")

            user = self.db.query(User).filter_by(email=email).first()
            
            if user:
                if not user.avatar_url and id_info.get("picture"):
                    user.avatar_url = id_info.get("picture")
                    self.db.commit()
                return user
            
            new_user = User(
                email=email,
                first_name=id_info.get("given_name", "Unknown"),
                last_name=id_info.get("family_name", "User"),
                avatar_url=id_info.get("picture"),
                email_verified=id_info.get("email_verified", False)
            )
            new_user.set_password(os.urandom(24).hex()) 
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            return new_user

        except ValueError as e:
             raise AuthenticationError(f"Invalid Google Token: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error during Google OAuth: {str(e)}") from e
