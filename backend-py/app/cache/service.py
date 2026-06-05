from typing import Any, Optional
from datetime import datetime

from src.logger import get_logger


class CacheService:

    def __init__(self):
        self.cache: dict[str, Any] = {}
        self.ttls: dict[str, float] = {}

    async def get(self, key: str) -> Optional[Any]:
        logger = get_logger()

        try:
            if key not in self.cache:
                await logger.debug("cache", f"Cache miss for key: {key}")
                return None

            if key in self.ttls and self.ttls[key] < datetime.utcnow().timestamp():
                del self.cache[key]
                del self.ttls[key]
                await logger.debug("cache", f"Cache entry expired: {key}")
                return None

            value = self.cache[key]
            await logger.debug("cache", f"Cache hit for key: {key}", {
                "additionalContext": {"size": len(str(value))}
            })
            return value

        except Exception as e:
            await logger.error("cache", f"Error retrieving from cache: {str(e)}", {
                "additionalContext": {"key": key}
            })
            return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        logger = get_logger()

        try:
            self.cache[key] = value

            if ttl_seconds:
                import time
                self.ttls[key] = time.time() + ttl_seconds

            ttl_str = f"{ttl_seconds}s" if ttl_seconds else "infinite"
            await logger.debug("cache", "Stored value in cache", {
                "additionalContext": {
                    "key": key,
                    "ttl": ttl_str,
                    "size": len(str(value))
                }
            })

        except Exception as e:
            await logger.error("cache", f"Error setting cache value: {str(e)}", {
                "additionalContext": {"key": key}
            })

    async def delete(self, key: str) -> None:
        logger = get_logger()

        try:
            if key not in self.cache:
                await logger.warn("cache", f"Attempted to delete non-existent cache key: {key}")
                return

            del self.cache[key]
            if key in self.ttls:
                del self.ttls[key]

            await logger.debug("cache", f"Deleted cache entry: {key}")

        except Exception as e:
            await logger.error("cache", f"Error deleting cache entry: {str(e)}", {
                "additionalContext": {"key": key}
            })

    async def clear(self) -> None:
        logger = get_logger()

        try:
            size = len(self.cache)
            self.cache.clear()
            self.ttls.clear()

            await logger.info("cache", "Cleared cache", {
                "additionalContext": {"entriesCleared": size}
            })

        except Exception as e:
            await logger.error("cache", f"Error clearing cache: {str(e)}")

    async def get_stats(self) -> dict:
        logger = get_logger()

        try:
            stats = {
                "size": len(self.cache),
                "keys": list(self.cache.keys())
            }

            await logger.debug("cache", "Cache statistics retrieved", {
                "additionalContext": stats
            })

            return stats

        except Exception as e:
            await logger.error("cache", f"Error getting cache stats: {str(e)}")
            raise


cache_service = CacheService()
