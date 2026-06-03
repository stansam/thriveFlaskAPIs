from functools import wraps
import logging
import redis as redis_lib
from flask import abort
from flask_login import UserMixin, current_user

from app.core.config import settings
from app.core.logging import get_logger
from app.core.errors.handlers import InsufficientRoleError
from app.enums import UserRole
from app.extensions import login_manager
from app.repository import user_repo
from app.models.user import User

logger = get_logger(__name__)

# Redis session denylist prefix
_SESSION_DENYLIST_PREFIX = "deactivated_session:"


def _get_redis():
    """Lazily obtain a Redis connection."""
    return redis_lib.from_url(
        settings.REDIS_URL,
        db=settings.REDIS_DENYLIST_DB,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
        socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
        decode_responses=True,
    )


def deactivate_user_session(user_id: str) -> None:
    """Mark the user's active sessions as deactivated in Redis."""
    try:
        r = _get_redis()
        r.set(f"{_SESSION_DENYLIST_PREFIX}{user_id}", "1", ex=2592000)
    except Exception as exc:
        logger.error(
            "Failed to set deactivation session in Redis for user %s: %s",
            user_id,
            exc,
        )


def reactivate_user_session(user_id: str) -> None:
    """Remove user's deactivated session status from Redis."""
    try:
        r = _get_redis()
        r.delete(f"{_SESSION_DENYLIST_PREFIX}{user_id}")
    except Exception as exc:
        logger.error(
            "Failed to delete deactivation session in Redis for user %s: %s",
            user_id,
            exc,
        )


def is_user_session_deactivated(user_id: str) -> bool:
    """Check if the user's sessions have been deactivated."""
    try:
        r = _get_redis()
        return r.exists(f"{_SESSION_DENYLIST_PREFIX}{user_id}") == 1
    except Exception as exc:
        logger.error(
            "Failed to check deactivation session in Redis for user %s: %s",
            user_id,
            exc,
        )
        return False


class FlaskLoginUser(UserMixin):
    """Thin adapter wrapping the domain User entity for Flask-Login."""

    def __init__(self, user: User) -> None:
        self._user = user

    def get_id(self) -> str:
        return self._user.id

    @property
    def is_active(self) -> bool:
        return self._user.is_active

    @property
    def domain_user(self) -> User:
        """Access underlying domain entity."""
        return self._user


@login_manager.user_loader
def load_user(user_id: str) -> FlaskLoginUser | None:
    """Load user by ID for Flask-Login, checking Redis denylist and account active status."""
    if is_user_session_deactivated(user_id):
        return None
    user = user_repo.get(user_id)
    if user is None or not user.is_active:
        return None
    return FlaskLoginUser(user)


def require_roles(*roles: UserRole):
    """Decorator: raise InsufficientRoleError if current_user.domain_user.role not in roles."""
    def decorator(f):
        @wraps(f)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.domain_user.role not in roles:
                required_roles_str = ", ".join(r.value for r in roles)
                raise InsufficientRoleError(required_role=required_roles_str)
            return f(*args, **kwargs)
        return decorated_view
    return decorator
