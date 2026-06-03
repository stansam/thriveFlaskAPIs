from __future__ import annotations
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from app.core.config import settings
from app.core.logging import get_logger
import secrets

logger = get_logger(__name__)


def generate_secure_random_password(length: int = 48) -> str:
    """
    Generate a cryptographically secure random password.
    Suitable for social login (OAuth) signup flows.
    """
    return secrets.token_urlsafe(length)


_hasher = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
)


def hash_password(plain: str) -> str:
    """Return an Argon2id digest of the plaintext password."""
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Return True if `plain` matches `hashed`.
    Never raises — returns False on any mismatch or error.
    Also transparently re-hashes if the stored hash uses outdated parameters
    (argon2-cffi calls this "needs rehash"); the caller is responsible for
    persisting the updated hash.
    """
    try:
        return _hasher.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, Exception):
        return False


def password_needs_rehash(hashed: str) -> bool:
    """True if the hash was created with older Argon2 parameters."""
    return _hasher.check_needs_rehash(hashed)

