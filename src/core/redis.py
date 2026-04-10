"""
Redis client for cache operations.
"""

from collections.abc import Awaitable
from typing import cast

from redis.asyncio import Redis

from src.core.config import settings


class RedisCacheHelper:
    """
    Redis cache operations with lazy connection.
    """

    def __init__(self) -> None:
        self._client: Redis | None = None

    async def _get_client(self) -> Redis:
        """
        Get or create Redis client.
        """
        if self._client is None:
            self._client = Redis.from_url(
                str(settings.REDIS.DSN),
                encoding="utf-8",
                decode_responses=True,
                health_check_interval=30,
            )
        return self._client

    async def close(self) -> None:
        """
        Close Redis connection.
        """
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, key: str) -> str | None:
        """
        Get value by key.
        """
        client = await self._get_client()
        return await client.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """
        Set key with expiration.
        """
        client = await self._get_client()
        return await client.setex(key, ttl, value)

    async def exists(self, key: str) -> bool:
        """
        Check if key exists.
        """
        client = await self._get_client()
        return await client.exists(key) > 0

    async def delete(self, key: str) -> int:
        """
        Delete key.
        """
        client = await self._get_client()
        return await client.delete(key)

    async def sadd(self, key: str, *values: str) -> int:
        """
        Add to set.
        """
        client = await self._get_client()
        return await cast(Awaitable[int], client.sadd(key, *values))

    async def srem(self, key: str, *values: str) -> int:
        """
        Remove from set.
        """
        client = await self._get_client()
        return await cast(Awaitable[int], client.srem(key, *values))

    async def smembers(self, key: str) -> set[str]:
        """
        Get set members.
        """
        client = await self._get_client()
        return await cast(Awaitable[set[str]], client.smembers(key))


# Global instance
redis_helper = RedisCacheHelper()
