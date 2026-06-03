from datetime import datetime, timezone
from typing import Any
import logging
from app.core.config import settings
from app.core.redis import get_redis
from app.core.errors.handlers import (
    PasswordResetTokenInvalidError,
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
)

logger = logging.getLogger(__name__)

_JWT_SECRET      = settings.JWT_SECRET_KEY
_JWT_ALGORITHM   = settings.JWT_ALGORITHM
_JWT_ISSUER      = settings.JWT_ISSUER
_JWT_AUDIENCE    = settings.JWT_AUDIENCE


def _utcnow_ts() -> int:
    """Current UTC timestamp as integer seconds (for JWT claims)."""
    return int(datetime.now(timezone.utc).timestamp())


# def create_access_token(
#     user_id: str,
#     role: str,
#     extra_claims: dict[str, Any] | None = None,
# ) -> str:
#     """
#     Issue a short-lived JWT access token.

#     Claims
#     ------
#     sub  — user_id
#     role — UserRole value string
#     iat  — issued-at (UTC seconds)
#     exp  — expiry (UTC seconds)
#     iss  — issuer
#     aud  — audience
#     typ  — "access"
#     """
#     now = _utcnow_ts()
#     payload: dict[str, Any] = {
#         "sub":  user_id,
#         "role": role,
#         "iat":  now,
#         "exp":  now + settings.JWT_ACCESS_TOKEN_EXPIRES_SECONDS,
#         "iss":  _JWT_ISSUER,
#         "aud":  _JWT_AUDIENCE,
#         "typ":  "access",
#     }
#     if extra_claims:
#         payload.update(extra_claims)
#     return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


# def create_refresh_token(user_id: str) -> str:
#     """
#     Issue a long-lived refresh token.
#     Contains minimal claims — only sub, iat, exp, typ.
#     """
#     now = _utcnow_ts()
#     payload: dict[str, Any] = {
#         "sub": user_id,
#         "iat": now,
#         "exp": now + settings.JWT_REFRESH_TOKEN_EXPIRES_SECONDS,
#         "iss": _JWT_ISSUER,
#         "aud": _JWT_AUDIENCE,
#         "typ": "refresh",
#     }
#     return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


# def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
#     """
#     Decode and validate a JWT.  Returns the payload dict.

#     Raises
#     ------
#     TokenExpiredError   — exp claim is in the past
#     TokenInvalidError   — any other JWT decode failure
#     TokenRevokedError   — token is in the Redis denylist
#     """
#     try:
#         payload = jwt.decode(
#             token,
#             _JWT_SECRET,
#             algorithms=[_JWT_ALGORITHM],
#             issuer=_JWT_ISSUER,
#             audience=_JWT_AUDIENCE,
#             options={"require": ["sub", "exp", "iat", "iss", "aud"]},
#         )
#     except jwt.ExpiredSignatureError:
#         raise TokenExpiredError()
#     except jwt.PyJWTError as exc:
#         logger.debug("JWT decode failed: %s", exc)
#         raise TokenInvalidError()

#     # Type check
#     if payload.get("typ") != expected_type:
#         raise TokenInvalidError(
#             f"Expected token type '{expected_type}', got '{payload.get('typ')}'."
#         )

#     # Denylist check
#     jti = payload.get("jti") or _token_jti(token)
#     if _is_token_revoked(jti):
#         raise TokenRevokedError()

#     return payload


# def _token_jti(token: str) -> str:
#     """Derive a stable identifier for a token (SHA-256 of raw bytes)."""
#     return hashlib.sha256(token.encode()).hexdigest()


# def extract_bearer_token() -> str | None:
#     """Extract the raw token from the Authorization: Bearer <token> header."""
#     auth_header = request.headers.get("Authorization", "")
#     if auth_header.startswith("Bearer "):
#         return auth_header[7:].strip()
#     return None
# token denylist using shared get_redis
# def revoke_token(token: str, expires_in_seconds: int | None = None) -> None:
#     """
#     Add a token to the Redis denylist.
#     `expires_in_seconds` should match the token's remaining TTL so Redis
#     auto-expires the key once the token would be invalid anyway.
#     """
#     jti = _token_jti(token)
#     ttl = expires_in_seconds or settings.JWT_ACCESS_TOKEN_EXPIRES_SECONDS
#     try:
#         get_redis().setex(f"denylist:{jti}", ttl, "1")
#     except Exception as exc:
#         # Log and continue — a Redis failure should not block logout
#         logger.error("Failed to add token to denylist: %s", exc)


# def _is_token_revoked(jti: str) -> bool:
#     """Return True if the JTI is found in the Redis denylist."""
#     try:
#         return get_redis().exists(f"denylist:{jti}") == 1
#     except Exception as exc:
#         logger.error("Redis denylist check failed: %s", exc)
#         return False  # fail open — don't break auth on Redis outage



