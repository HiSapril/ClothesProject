import redis
import json
import logging
from typing import Any, Optional, Union
from app.core.config import settings

logger = logging.getLogger("app")

class Cache:
    """
    Centralized caching utility with selective Redis backend.
    If Redis is unavailable or caching is disabled, it fails gracefully.
    """
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._memory_cache = {}
        if not settings.ENABLE_CACHING:
            logger.info("Caching is globally disabled via settings.")
            return

        try:
            self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Test connection
            self.client.ping()
            logger.info("Cache initialized successfully (Redis backend).")
        except Exception as e:
            logger.info(f"Cache initialization failed: {e}. Falling back to In-Memory cache.")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        if not settings.ENABLE_CACHING:
            return None
        if not self.client:
            return self._memory_cache.get(key)
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return self._memory_cache.get(key)
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value with TTL (default 5 minutes)"""
        if not settings.ENABLE_CACHING:
            return False
        if not self.client:
            self._memory_cache[key] = value
            return True
        try:
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            self._memory_cache[key] = value
            return True

    def delete(self, key: str):
        if not self.client:
            return
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")

# Global singleton
cache = Cache()
