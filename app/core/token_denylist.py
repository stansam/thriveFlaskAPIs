"""
Token denylist — single-use invalidation for password-reset tokens.

Provides an `ITokenDenylist` interface and a Redis-backed implementation
that stores the SHA-256 fingerprint of consumed tokens with an expiry TTL
matching `settings.JWT_RESET_TOKEN_EXPIRES_SECONDS`.

Why SHA-256 of the token?
    The raw token contains the user_id and timestamp in plain text.
    Storing only the fingerprint avoids unnecessary PII in Redis keys
    and prevents token recovery from the denylist.

Why Redis instead of the database?
    - Pure cache concern: no relational joins needed
    - TTL auto-evicts old entries — no cleanup job required
    - O(1) lookup per request
"""
from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

_DENYLIST_PREFIX = "reset_token_used:"


class ITokenDenylist(ABC):
    """Abstract interface for single-use token invalidation."""

    @abstractmethod
    def consume(self, token: str, ttl_seconds: int) -> bool:
        """Mark a token as consumed.

        Args:
            token: The raw token string to invalidate.
            ttl_seconds: Seconds until auto-eviction from store.

        Returns:
            True if this was the FIRST consumption (token was valid and unused).
            False if the token was already consumed (replay attack).
        """
        ...

    @abstractmethod
    def is_consumed(self, token: str) -> bool:
        """Return True if the token has already been consumed."""
        ...


class RedisTokenDenylist(ITokenDenylist):
    """Redis-backed token denylist.

    Uses a Redis SET-NX (Set if Not eXist) pattern to atomically detect
    and mark the first use. Replayed tokens are rejected.

    The Redis connection is resolved lazily to avoid circular imports or
    app-context errors at module load time.
    """

    def _key(self, token: str) -> str:
        """Derive a Redis key from the token fingerprint."""
        digest = hashlib.sha256(token.encode()).hexdigest()
        return f"{_DENYLIST_PREFIX}{digest}"

    def _redis(self):  # type: ignore[return]
        """Lazily obtain a Redis connection from Flask-Caching / redis-py."""
        try:
            import redis as redis_lib
            from app.core.config import settings
            return redis_lib.from_url(
                settings.REDIS_URL,
                db=settings.REDIS_DENYLIST_DB,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                decode_responses=True,
            )
        except Exception:  # pragma: no cover
            logger.exception("Redis connection failed in token denylist.")
            raise

    def consume(self, token: str, ttl_seconds: int) -> bool:
        """Atomically mark token as consumed and set TTL.

        Uses SET key value NX EX which is atomic in Redis — no TOCTOU gap.

        Returns:
            True if this is the first use (token accepted).
            False if already consumed (replay detected).
        """
        r = self._redis()
        key = self._key(token)
        was_set: bool = r.set(key, "1", nx=True, ex=ttl_seconds) is not None
        if not was_set:
            logger.warning(
                "Reset token replay detected. Key already exists: %s",
                key,
            )
        return was_set

    def is_consumed(self, token: str) -> bool:
        """Return True if the token key already exists in Redis."""
        r = self._redis()
        return r.exists(self._key(token)) == 1


class NullTokenDenylist(ITokenDenylist):
    """No-op denylist for testing environments without Redis.

    WARNING: Not for production use. Tokens can be replayed.
    """

    def consume(self, token: str, ttl_seconds: int) -> bool:  # noqa: ARG002
        return True

    def is_consumed(self, token: str) -> bool:  # noqa: ARG002
        return False
