"""
Application-level symmetric encryption for sensitive model fields.

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the `cryptography` package.
The encryption key is read from settings.MFA_ENCRYPTION_KEY.

If the key is not configured (development), encryption is a no-op.
"""
from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_fernet():
    """Return a Fernet instance, or None if encryption is not configured."""
    from app.core.config import settings
    key = settings.MFA_ENCRYPTION_KEY
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        logger.error("Failed to initialise Fernet encryption: %s", exc)
        raise


def encrypt_field(value: str | None) -> str | None:
    """
    Encrypt a string field value. Returns the ciphertext as a string.
    If encryption is not configured, returns the value unchanged.
    """
    if value is None:
        return None
    fernet = _get_fernet()
    if fernet is None:
        return value  # no-op in dev without key
    return fernet.encrypt(value.encode()).decode()


def decrypt_field(value: str | None) -> str | None:
    """
    Decrypt a string field value. Returns the plaintext.
    If encryption is not configured, returns the value unchanged.
    Raises ValueError if decryption fails (tampered ciphertext).
    """
    if value is None:
        return None
    fernet = _get_fernet()
    if fernet is None:
        return value  # no-op in dev without key
    try:
        return fernet.decrypt(value.encode()).decode()
    except Exception as exc:
        logger.error("MFA secret decryption failed: %s", exc)
        raise ValueError("Failed to decrypt mfa_secret — key mismatch or tampered data.") from exc
