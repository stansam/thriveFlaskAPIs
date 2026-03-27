from __future__ import annotations
import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from app.core.config import settings


logger = logging.getLogger(__name__)


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

