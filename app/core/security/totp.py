from __future__ import annotations
import pyotp
from argon2.exceptions import VerificationError, VerifyMismatchError
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def generate_totp_secret() -> str:
    """Generate a new base-32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_provisioning_uri(secret: str, user_email: str) -> str:
    """Return an otpauth:// URI suitable for QR code generation."""
    totp = pyotp.TOTP(secret, digits=settings.TOTP_DIGITS, interval=settings.TOTP_INTERVAL)
    return totp.provisioning_uri(
        name=user_email,
        issuer_name=settings.TOTP_ISSUER_NAME,
    )


def verify_totp(secret: str, code: str) -> bool:
    """
    Verify a TOTP code against a secret.
    Allows ±1 interval window to handle clock skew.
    """
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret, digits=settings.TOTP_DIGITS, interval=settings.TOTP_INTERVAL)
    return totp.verify(code, valid_window=1)


def generate_totp_qr_data_url(provisioning_uri: str) -> str:
    """
    Render a QR code for the provisioning URI and return a base-64 data URL.
    Requires `qrcode[pil]` package.
    Falls back to returning the URI as a data URL if qrcode is not installed.
    """
    try:
        import io
        import base64
        import qrcode  # type: ignore
        from qrcode.image.pil import PilImage

        img = qrcode.make(provisioning_uri, image_factory=PilImage)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{encoded}"
    except ImportError:
        logger.warning("qrcode[pil] not installed; returning URI as data URL.")
        import base64
        encoded = base64.b64encode(provisioning_uri.encode()).decode()
        return f"data:text/plain;base64,{encoded}"


_TOTP_USED_PREFIX = "totp_used:"
_TOTP_REPLAY_TTL = 90  # seconds — covers valid_window=1 (3 × 30s intervals)


def is_totp_replayed(user_id: str, code: str) -> bool:
    """
    Check if the (user_id, code) pair has been used in the last _TOTP_REPLAY_TTL seconds.

    Returns True if this is a replay (should be REJECTED).
    Returns False if this is a fresh code (should be ACCEPTED after other checks pass).
    """
    try:
        from app.core.redis import get_redis
        r = get_redis()
        key = f"{_TOTP_USED_PREFIX}{user_id}:{code}"
        return r.exists(key) == 1
    except Exception as exc:
        logger.error(
            "TOTP replay check failed for user %s: %s — allowing (fail-open).",
            user_id,
            exc,
        )
        # Fail-open: if Redis is unavailable, allow the code through
        # to avoid locking out users due to infrastructure failure
        return False


def record_totp_use(user_id: str, code: str) -> None:
    """
    Record that a TOTP code has been used for a user.
    Call this ONLY AFTER a code has been verified as valid.
    """
    try:
        from app.core.redis import get_redis
        r = get_redis()
        key = f"{_TOTP_USED_PREFIX}{user_id}:{code}"
        r.set(key, "1", ex=_TOTP_REPLAY_TTL)
    except Exception as exc:
        logger.error(
            "Failed to record TOTP use for user %s (replay protection may be reduced): %s",
            user_id,
            exc,
        )


