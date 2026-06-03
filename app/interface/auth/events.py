# app/interface/auth/events.py
"""
Event subscribers for Auth domain events.
"""
from __future__ import annotations

from app.core.events import subscribe
from app.core.events.dataclass import (
    UserLoggedInEvent,
    UserLoggedOutEvent,
    PasswordChangedEvent,
    PasswordResetRequestedEvent,
    PasswordResetCompletedEvent,
    MFAEnrolledEvent,
    MFADisabledEvent,
)
from app.core.dependencies import get_services
from app.enums import NotificationEventType, RecipientType
from app.core.logging import get_logger

logger = get_logger(__name__)


@subscribe(UserLoggedInEvent)
def on_user_logged_in(event: UserLoggedInEvent) -> None:
    """Log successful user login."""
    logger.info(
        "User logged in: user_id=%s ip=%s agent=%s",
        event.user_id,
        event.ip_address,
        event.user_agent,
    )


@subscribe(UserLoggedOutEvent)
def on_user_logged_out(event: UserLoggedOutEvent) -> None:
    """Log successful user logout."""
    logger.info("User logged out: user_id=%s", event.user_id)


@subscribe(PasswordChangedEvent)
def on_password_changed(event: PasswordChangedEvent) -> None:
    """Log password change and dispatch notification."""
    logger.warning("Password changed for user_id=%s", event.user_id)
    try:
        get_services().notification.dispatch(
            event_type=NotificationEventType.USER_PASSWORD_CHANGED,
            recipient_type=RecipientType.USER,
            recipient_id=event.user_id,
            context={"user_id": event.user_id},
        )
    except Exception as exc:
        logger.error(
            "Failed to dispatch password changed notification for user %s: %s",
            event.user_id,
            exc,
        )


@subscribe(PasswordResetRequestedEvent)
def on_password_reset_requested(event: PasswordResetRequestedEvent) -> None:
    """Log password reset request and dispatch reset link email (secret-in-transit reset_token)."""
    logger.info("Password reset requested for user_id=%s", event.user_id)
    try:
        # Crucial to delivery: if this subscriber fails, the reset token is lost.
        get_services().notification.dispatch(
            event_type=NotificationEventType.USER_PASSWORD_RESET,
            recipient_type=RecipientType.USER,
            recipient_id=event.user_id,
            context={
                "reset_token": event.reset_token,  # secret-in-transit
                "email": event.email,
                "user_id": event.user_id,
            },
        )
    except Exception as exc:
        logger.error(
            "Failed to dispatch password reset notification for user %s: %s",
            event.user_id,
            exc,
        )


@subscribe(PasswordResetCompletedEvent)
def on_password_reset_completed(event: PasswordResetCompletedEvent) -> None:
    """Log password reset completion."""
    logger.info("Password reset completed for user_id=%s", event.user_id)


@subscribe(MFAEnrolledEvent)
def on_mfa_enrolled(event: MFAEnrolledEvent) -> None:
    """Log MFA enrollment and dispatch notification."""
    logger.info("MFA enrolled for user_id=%s", event.user_id)
    try:
        get_services().notification.dispatch(
            event_type=NotificationEventType.USER_MFA_ENROLLED,
            recipient_type=RecipientType.USER,
            recipient_id=event.user_id,
            context={"user_id": event.user_id},
        )
    except Exception as exc:
        logger.error(
            "Failed to dispatch MFA enrolled notification for user %s: %s",
            event.user_id,
            exc,
        )


@subscribe(MFADisabledEvent)
def on_mfa_disabled(event: MFADisabledEvent) -> None:
    """Log MFA deactivation and dispatch security notification."""
    logger.warning("MFA disabled for user_id=%s", event.user_id)
    try:
        get_services().notification.dispatch(
            event_type=NotificationEventType.USER_MFA_DISABLED,
            recipient_type=RecipientType.USER,
            recipient_id=event.user_id,
            context={"user_id": event.user_id},
        )
    except Exception as exc:
        logger.error(
            "Failed to dispatch MFA disabled notification for user %s: %s",
            event.user_id,
            exc,
        )
