import secrets
from datetime import datetime, timezone, timedelta
from typing import Tuple

def generate_secure_token(hours_valid: int = 24) -> Tuple[str, datetime]:
    """
    Generate an opaque 64-character URL-safe string coupled perfectly to 
    a UTC expiration date natively scaling for reset or verification links uniformly.
    """
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=hours_valid)
    return token, expires_at
