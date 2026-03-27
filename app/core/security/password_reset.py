import hashlib
import hmac
import time
import logging

from app.core.errors.handlers import PasswordResetTokenInvalidError
from app.core.config import settings

logger = logging.getLogger(__name__)

_RESET_SEP = "."


def create_reset_token(user_id: str) -> str:
    """
    Create a time-limited password reset token.

    Format: <user_id>.<timestamp>.<hmac_signature>

    The timestamp is seconds since epoch; the signature covers
    user_id + timestamp so the token cannot be replayed for a
    different user or after it expires.
    """
    ts = str(int(time.time()))
    payload = f"{user_id}{_RESET_SEP}{ts}"
    sig = hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}{_RESET_SEP}{sig}"


def verify_reset_token(token: str) -> str:
    """
    Validate a reset token and return the user_id.

    Raises `PasswordResetTokenInvalidError` if the token is malformed,
    the signature is invalid, or the token has expired.
    """
    try:
        parts = token.split(_RESET_SEP)
        if len(parts) != 3:
            raise ValueError("Wrong number of parts.")

        user_id, ts_str, sig = parts
        payload = f"{user_id}{_RESET_SEP}{ts_str}"
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(sig, expected_sig):
            raise ValueError("Signature mismatch.")

        issued_at = int(ts_str)
        if time.time() - issued_at > settings.JWT_RESET_TOKEN_EXPIRES_SECONDS:
            raise ValueError("Token expired.")

        return user_id
    except (ValueError, TypeError) as exc:
        logger.debug("Reset token invalid: %s", exc)
        raise PasswordResetTokenInvalidError()
