"""
Token-specific Redis cache operations using the core Redis helper.
"""

from src.core.redis import RedisCacheHelper, redis_helper


class TokenCacheService:
    """
    Redis cache service for token management operations.
    """

    def __init__(self, redis: RedisCacheHelper = redis_helper) -> None:
        self.redis = redis

    # Refresh Token Operations
    async def store_refresh_token(self, token: str, user_id: str, ttl_seconds: int) -> bool:
        """
        Store refresh token in Redis with TTL.
        Args:
            token: Refresh token string
            user_id: User ID
            ttl_seconds: Time to live in seconds
        Returns:
            bool: True if stored successfully
        """
        return await self.redis.setex(f"refresh:{token}", ttl_seconds, user_id)

    async def get_user_from_refresh_token(self, token: str) -> str | None:
        """
        Get user ID from refresh token.
        Args:
            token: Refresh token string
        Returns:
            str | None: User ID if token exists, None otherwise
        """
        return await self.redis.get(f"refresh:{token}")

    async def delete_refresh_token(self, token: str) -> bool:
        """
        Delete refresh token from Redis.
        Args:
            token: Refresh token string
        Returns:
            bool: True if deleted successfully
        """
        return bool(await self.redis.delete(f"refresh:{token}"))

    # Access Token Blacklist Operations
    async def blacklist_access_token(self, token: str, ttl_seconds: int) -> bool:
        """
        Add access token to blacklist with TTL.
        Args:
            token: Access token to blacklist
            ttl_seconds: Time to live (should match token expiry)
        Returns:
            bool: True if blacklisted successfully
        """
        return await self.redis.setex(f"blacklist:{token}", ttl_seconds, "revoked")

    async def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if access token is blacklisted.
        Args:
            token: Access token to check
        Returns:
            bool: True if token is blacklisted
        """
        return await self.redis.exists(f"blacklist:{token}")

    # User Session Management
    async def add_user_session(self, user_id: str, refresh_token: str) -> bool:
        """
        Add refresh token to user's active sessions.
        Args:
            user_id: User ID
            refresh_token: Refresh token
        Returns:
            bool: True if added successfully
        """
        return bool(await self.redis.sadd(f"user:{user_id}:sessions", refresh_token))

    async def remove_user_session(self, user_id: str, refresh_token: str) -> bool:
        """
        Remove refresh token from user's active sessions.
        Args:
            user_id: User ID
            refresh_token: Refresh token
        Returns:
            bool: True if removed successfully
        """
        return bool(await self.redis.srem(f"user:{user_id}:sessions", refresh_token))
