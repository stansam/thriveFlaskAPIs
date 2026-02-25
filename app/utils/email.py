from app.services.notification.service import NotificationService
from flask import current_app, url_for
from app.extensions import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_email_service():
    return NotificationService()

def send_welcome_email(user):
    """Sends a welcome email to the newly registered user."""
    try:
        dashboard_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/dashboard"
        service = get_email_service()
        body = service.render_template(
            "welcome_email.html",
            context={
                "user": user,
                "year": datetime.now().year,
                "dashboard_url": dashboard_url
            }
        )
        service.send_email(
            to_email=user.email,
            subject="Welcome to Thrive Travels!",
            body_html=body
        )
        logger.info(f"Welcome email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")
        return False

def send_verification_email(user, token):
    """Sends an email verification link."""
    try:
        service = get_email_service()
        verification_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={token}&user_id={user.id}"
        
        body = service.render_template(
            "verify_email.html",
            context={
                "user": user,
                "token": token,
                "verification_url": verification_url,
                "year": datetime.now().year
            }
        )
        service.send_email(
            to_email=user.email,
            subject="Verify Your Email - Thrive Travels",
            body_html=body
        )
        logger.info(f"Verification email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return False

def send_password_reset_email(user, token):
    """Sends a password reset link."""
    try:
        service = get_email_service()
        reset_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}&email={user.email}"
        
        body = service.render_template(
            "reset_password.html",
            context={
                "user": user,
                "reset_url": reset_url,
                "year": datetime.now().year
            }
        )
        service.send_email(
            to_email=user.email,
            subject="Reset Your Password - Thrive Travels",
            body_html=body
        )
        logger.info(f"Password reset email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        return False
