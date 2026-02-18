import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Caching will be in-memory only (per process).")

class CacheService:
    _instance = None
    _local_cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheService, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self.redis_client = None
        if REDIS_AVAILABLE:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info(f"Connected to Redis at {redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                return self._local_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, timeout: int = 300):
        try:
            if self.redis_client:
                self.redis_client.setex(key, timeout, json.dumps(value))
            else:
                self._local_cache[key] = value
                # Note: Local cache doesn't implement expiry in this simple version
        except Exception as e:
            logger.error(f"Cache set error: {e}")

cache = CacheService()
