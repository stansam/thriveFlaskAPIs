from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from typing import Optional

def get_serializer() -> URLSafeTimedSerializer:
    """Retrieves securely bound serializer from Flask physical configs natively."""
    secret_key = current_app.config.get('SECRET_KEY', 'fallback_secret')
    return URLSafeTimedSerializer(secret_key)

def generate_secure_token(payload: str) -> str:
    """
    Generates a cryptographically signed payload matching `itsdangerous` boundaries. 
    It embeds the payload logically inside the physical token signature natively.
    """
    serializer = get_serializer()
    return serializer.dumps(payload, salt='auth-token-salt')

def verify_secure_token(token: str, max_age_seconds: int) -> Optional[str]:
    """
    Extracts the physical payload from the signature verifying its lifespan
    and integrity securely without database bounds.
    """
    serializer = get_serializer()
    try:
        data = serializer.loads(token, salt='auth-token-salt', max_age=max_age_seconds)
        return data
    except (SignatureExpired, BadSignature):
        return None
