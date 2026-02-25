from typing import Tuple, Optional
from datetime import datetime, timezone, timedelta
from flask_login import login_user
from app.models.user import User
from app.repository import repositories
from app.dto.auth.schemas import LoginRequestDTO, RegisterRequestDTO
from app.services.auth.utils import generate_secure_token, verify_secure_token
from flask import request, current_app
import logging
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO

logger = logging.getLogger(__name__)
class AuthService:
    """
    AuthService orchestrates the high-level business flows for user
    sessions mapping directly on top of the generic UserRepository logic.
    """

    def __init__(self):
        # Service strictly queries Repositories—not raw db.session mappings.
        self.user_repo = repositories.user

    def login_user(self, credentials: LoginRequestDTO) -> Tuple[bool, Optional[User]]:
        """
        Validates the literal password against `check_password_hash` safely
        and utilizes native Flash-Login to establish the session variable.
        """
        user = self.user_repo.find_by_email(credentials.email)
        if not user or not user.check_password(credentials.password):
            return False, None
            
        # Hook up into Flask-Login. remember=True ensures session cookies outlast browser tab closures natively
        login_user(user, remember=credentials.remember)
        
        # Optionally bump their last_login tracker timestamp silently
        user.last_login = datetime.now(timezone.utc)
        self.user_repo.update(user.id, {"last_login": user.last_login}, commit=True)
        return True, user

    def register_user(self, data: RegisterRequestDTO) -> User:
        """
        Interrogates for duplicate emails, creates the record cleanly masking the password hash 
        natively via User.set_password, and triggers the async welcoming notifications.
        """
        existing = self.user_repo.find_by_email(data.email)
        if existing:
            raise ValueError("Email address already registered.")
            
        token = generate_secure_token(data.email)
        
        user_dict = {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "email": data.email,
            "phone": data.phone,
            "role": data.role,
            "gender": data.gender,
            "locale": data.locale,
            "company_id": data.company_id,
            "email_verification_token": None,
            "email_verification_token_expires_at": None,
            "email_verified": False
        }
        
        # Construct cleanly and hash immediately avoiding bare passwords ever living in memory
        user = User(**user_dict)
        user.set_password(data.password)
        
        # Instruct repo to just append and commit the completely assembled object natively
        created_user = self.user_repo.save_user(user)
        
        try:
            ns = NotificationService()
            # Explicitly construct the verification URL bounding the token payload securely
            verification_link = f"{request.host_url}api/auth/verify-email?token={token}"
            ns.dispatch_notification(DispatchNotificationDTO(
                user_id=created_user.id,
                trigger_event="WELCOME_EMAIL",
                context={
                    "first_name": created_user.first_name,
                    "verification_link": verification_link
                }
            ))
        except Exception as e:
            logger.error(f"Failed dispatching physical Welcome payload natively: {e}")
            
        return created_user

    def verify_email(self, token: str) -> bool:
        """Checks cryptographic token boundaries and flags email ownership definitively."""
        email = verify_secure_token(token, max_age_seconds=48 * 3600)
        if not email:
            return False # Token invalid or lapsed natively
            
        user = self.user_repo.find_by_email(email)
        if not user:
            return False
            
        self.user_repo.update(
            user.id, 
            {
                "email_verified": True,
                "email_verification_token": None,
                "email_verification_token_expires_at": None
            }, 
            commit=True
        )
        return True

    def request_password_reset(self, email: str) -> bool:
        """Issues the highly sensitive temporary link sent out-of-band to user contacts cryptographically."""
        user = self.user_repo.find_by_email(email)
        if not user:
            # Silently return True returning no hints back to bad actors guessing random emails
            return True 
            
        # Cryptographic link binding email payload dynamically. DB saves omitted permanently
        token = generate_secure_token(user.email)
        try:
            ns = NotificationService()
            reset_link = f"{request.host_url}api/auth/reset-password?token={token}"
            ns.dispatch_notification(DispatchNotificationDTO(
                user_id=user.id,
                trigger_event="PASSWORD_RESET_REQUESTED",
                context={
                    "first_name": user.first_name,
                    "reset_link": reset_link
                }
            ))
        except Exception as e:
            logger.error(f"Failed dispatching physical Password Reset natively: {e}")
            
        return True

    def reset_password(self, token: str, new_password: str) -> bool:
        """Consumes the cryptographic link confirming reset access authority securely."""
        email = verify_secure_token(token, max_age_seconds=2 * 3600)
        if not email:
            return False # Token invalid or lapsed natively
            
        user = self.user_repo.find_by_email(email)
        if not user:
            return False
            
        user.set_password(new_password)
        self.user_repo.update(
            user.id, 
            {
                "password_hash": user.password_hash, # Updating the repo mapping strictly
                "email_verification_token": None,
                "email_verification_token_expires_at": None
            }, 
            commit=True
        )
        return True
