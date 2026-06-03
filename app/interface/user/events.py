# app/interface/user/events.py
"""
Event subscribers for User domain events.
"""
from __future__ import annotations

from app.core.events import subscribe
from app.core.events.dataclass import (
    UserCreatedEvent,
    UserUpdatedEvent,
    UserDeactivatedEvent,
    UserReactivatedEvent,
    UserPreferenceUpdatedEvent,
)
from app.core.dependencies import get_services
from app.enums import NotificationEventType, RecipientType
from app.core.auth_user import deactivate_user_session, reactivate_user_session
from app.core.logging import get_logger

logger = get_logger(__name__)


@subscribe(UserCreatedEvent)
def on_user_created(event: UserCreatedEvent) -> None:
    """Log user creation and dispatch welcome notifications via system/in-app and email channels."""
    logger.info(
        "User created: user_id=%s email=%s role=%s by actor=%s",
        event.user_id,
        event.email,
        event.role,
        event.actor_id,
    )
    try:
        context = {
            "user_id": event.user_id,
            "email": event.email,
            "role": event.role,
            "full_name": event.full_name,
        }
        get_services().notification.dispatch(
            event_type=NotificationEventType.USER_CREATED,
            recipient_type=RecipientType.USER,
            recipient_id=event.user_id,
            context=context,
        )
    except Exception as exc:
        logger.error(
            "Failed to dispatch welcome notification for user %s: %s",
            event.user_id,
            exc,
        )


@subscribe(UserUpdatedEvent)
def on_user_updated(event: UserUpdatedEvent) -> None:
    """Log user profile updates."""
    logger.info(
        "User updated: user_id=%s fields=%s by actor=%s",
        event.user_id,
        event.changed_fields,
        event.actor_id,
    )


@subscribe(UserDeactivatedEvent)
def on_user_deactivated(event: UserDeactivatedEvent) -> None:
    """Log user deactivation and invalidate active user sessions immediately."""
    logger.warning(
        "User deactivated: user_id=%s by actor=%s",
        event.user_id,
        event.actor_id,
    )
    try:
        deactivate_user_session(event.user_id)
    except Exception as exc:
        logger.error(
            "Failed to invalidate sessions on deactivation for user %s: %s",
            event.user_id,
            exc,
        )


@subscribe(UserReactivatedEvent)
def on_user_reactivated(event: UserReactivatedEvent) -> None:
    """Log user reactivation and restore session validity."""
    logger.info(
        "User reactivated: user_id=%s by actor=%s",
        event.user_id,
        event.actor_id,
    )
    try:
        reactivate_user_session(event.user_id)
    except Exception as exc:
        logger.error(
            "Failed to restore sessions on reactivation for user %s: %s",
            event.user_id,
            exc,
        )


@subscribe(UserPreferenceUpdatedEvent)
def on_preference_updated(event: UserPreferenceUpdatedEvent) -> None:
    """Log user preference updates."""
    logger.info(
        "User preferences updated: user_id=%s fields=%s by actor=%s",
        event.user_id,
        event.changed_fields,
        event.actor_id,
    )
