"""
Redis-backed IP-level login attempt tracker for brute-force protection.

Tracks failed login attempts by IP address. Independent of account-level
lockout — provides a second layer of defense against distributed attacks.
"""
from __future__ import annotations

import redis as redis_lib
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_IP_ATTEMPTS_PREFIX = "login_fail:"
_IP_LOCKOUT_PREFIX  = "login_lock:"

_IP_LOCKOUT_THRESHOLD = 20      # attempts before IP lockout
_IP_LOCKOUT_WINDOW_SECONDS = 60 * 60  # 1-hour window for attempt count
_IP_LOCKOUT_DURATION_SECONDS = 60 * 30  # 30-minute IP lockout


def _get_redis():
    return redis_lib.from_url(
        settings.REDIS_URL,
        db=settings.REDIS_DENYLIST_DB,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
        socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
        decode_responses=True,
    )


def record_failed_attempt(ip_address: str) -> int:
    """
    Record a failed login attempt from an IP. Returns the current count.
    Counter resets after _IP_LOCKOUT_WINDOW_SECONDS.
    """
    if not ip_address:
        return 0
    try:
        r = _get_redis()
        key = f"{_IP_ATTEMPTS_PREFIX}{ip_address}"
        count = r.incr(key)
        if count == 1:
            r.expire(key, _IP_LOCKOUT_WINDOW_SECONDS)
        if count >= _IP_LOCKOUT_THRESHOLD:
            lock_key = f"{_IP_LOCKOUT_PREFIX}{ip_address}"
            r.set(lock_key, "1", ex=_IP_LOCKOUT_DURATION_SECONDS)
            logger.warning(
                "IP %s locked out after %d failed login attempts.", ip_address, count
            )
        return count
    except Exception as exc:
        logger.error("login_guard.record_failed_attempt failed for IP %s: %s", ip_address, exc)
        return 0


def is_ip_locked(ip_address: str) -> bool:
    """Return True if the IP is currently under lockout."""
    if not ip_address:
        return False
    try:
        r = _get_redis()
        return r.exists(f"{_IP_LOCKOUT_PREFIX}{ip_address}") == 1
    except Exception as exc:
        logger.error("login_guard.is_ip_locked failed for IP %s: %s", ip_address, exc)
        return False


def clear_attempts(ip_address: str) -> None:
    """Clear attempt counter for an IP on successful login."""
    if not ip_address:
        return
    try:
        r = _get_redis()
        r.delete(f"{_IP_ATTEMPTS_PREFIX}{ip_address}")
    except Exception as exc:
        logger.error("login_guard.clear_attempts failed for IP %s: %s", ip_address, exc)
        return
