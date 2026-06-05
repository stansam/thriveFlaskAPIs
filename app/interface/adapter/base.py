import uuid
from typing import Any
import hashlib
from redis import Redis

from flask import g, has_request_context
from app.core.config import settings
from app.core.redis import get_redis
from app.interface._base import BaseService
from app.core.logging import get_logger
from app.core.errors.handlers import ExternalServiceError

logger = get_logger(__name__)

class AdapterBaseService(BaseService):

    def __init__(self) -> None:
        self._base_url = f"https://{settings.RAPIDAPI_KAYAK_HOST}"
        self._headers = {
            "X-RapidAPI-Key":  settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": settings.RAPIDAPI_KAYAK_HOST,
            "Content-Type":    "application/json",
        }
        self._redis = self._init_redis()

    def _init_redis(self) -> Redis | None:
        if not settings.REDIS_URL:
            return None
        try:
            return get_redis()
        except Exception as exc:
            logger.warning("Redis init failed, cache disabled: %s", exc)
            return None

    def _guard_api_key(self) -> bool:
        if settings.RAPIDAPI_KEY:
            return True
        if settings.FLASK_ENV.lower() not in ("development", "testing"):
            raise ExternalServiceError(
                service="Kayak",
                message="RAPIDAPI_KEY is not configured. Flight search unavailable.",
            )
        logger.warning("RAPIDAPI_KEY not set — returning mock flight results.")
        return False

    def _safe_headers(self) -> dict[str, str]:
        headers = self._request_headers()
        if "X-RapidAPI-Key" in headers:
            headers["X-RapidAPI-Key"] = "REDACTED"
        return headers

    def _request_headers(self) -> dict[str, str]:
        headers = dict(self._headers)
        if has_request_context():
            headers["X-Request-ID"] = getattr(g, "request_id", str(uuid.uuid4()))
        return headers
    
    def _cache_key(self, prefix: str, *args: Any) -> str:
        key_str = "|".join(str(a) for a in args)
        digest = hashlib.sha256(key_str.encode()).hexdigest()
        return f"{prefix}:{digest}"