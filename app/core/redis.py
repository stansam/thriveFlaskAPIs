# app/core/redis.py
"""
Shared Redis connection factory.
Ensures all modules use a central Redis client configured from settings.
"""
from __future__ import annotations

import redis as redis_lib
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_redis() -> redis_lib.Redis:
    """
    Return a Redis client configured from application settings.
    Uses the denylist DB index by default.
    """
    return redis_lib.from_url(
        settings.REDIS_URL,
        db=settings.REDIS_DENYLIST_DB,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
        socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
        decode_responses=True,
    )
