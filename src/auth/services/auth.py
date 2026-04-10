from datetime import UTC, datetime, timedelta
from uuid import UUID

from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.crud.user import crud_user
from src.auth.exceptions import (
    InvalidCredentialsException,
    TokenValidationException,
    UserNotFoundException,
)
from src.auth.models import User
from src.auth.schemas.user import TokenSchema
from src.auth.services.token_cache import TokenCacheService
from src.auth.utils import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    generate_refresh_token,
    verify_password,
    verify_token_with_blacklist,
)
from src.core.config import settings


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.token_cache = TokenCacheService()

    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password.
        Uses constant-time operations to prevent timing attacks.
        Args:
            email (str): User email
            password (str): Plain text password
        Returns:
            User: Authenticated user
        Raises:
            InvalidCredentialsException: If credentials are invalid
        """
        user = await crud_user.get_by_email(db=self.db, email=email)

        # Always perform password verification to prevent timing attacks
        # Use a dummy hash if user doesn't exist
        password_hash = user.password if user else DUMMY_PASSWORD_HASH
        password_valid = verify_password(plain_password=password, hashed_password=password_hash)

        if not user or not password_valid:
            raise InvalidCredentialsException()
        return user

    async def create_session_tokens(self, user: User) -> TokenSchema:
        """
        Create access token and optional refresh token using Redis.
        Args:
            user (User): User object
        Returns:
            TokenSchema: Access and refresh token response
        """
        # Create access token (short-lived)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

        # Create refresh token (long-lived)
        refresh_token = generate_refresh_token()
        refresh_ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

        # Store refresh token in Redis
        await self.token_cache.store_refresh_token(
            token=refresh_token, user_id=str(user.id), ttl_seconds=refresh_ttl_seconds
        )

        # Track user session
        await self.token_cache.add_user_session(user_id=str(user.id), refresh_token=refresh_token)

        return TokenSchema(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    async def login(self, email: str, password: str) -> TokenSchema:
        """
        Login user and return access token.
        Args:
            email (str): User email
            password (str): Plain text password
        Returns:
            Token: Access token response
        Raises:
            InvalidCredentialsException: If credentials are invalid
        """
        user = await self.authenticate_user(email=email, password=password)
        return await self.create_session_tokens(user=user)

    async def get_current_user(self, token: str) -> User:
        """
        Get current user from JWT token with Redis blacklist checking.
        Args:
            token (str): JWT token
        Returns:
            User: Current authenticated user
        Raises:
            TokenValidationException: If token is invalid, expired, or blacklisted
            UserNotFoundException: If user not found
        """
        try:
            token_data = await verify_token_with_blacklist(token=token)
        except InvalidTokenError as e:
            raise TokenValidationException() from e

        user = await crud_user.get(db=self.db, id=token_data.user_id)
        if not user:
            raise UserNotFoundException(user_id=str(token_data.user_id))

        return user

    async def logout(self, token: str) -> bool:
        """
        Logout user by blacklisting the access token.
        Args:
            token (str): Access token to blacklist
        Returns:
            bool: True if logout successful
        Raises:
            TokenValidationException: If token is invalid
        """
        try:
            # Verify token first to ensure it's valid
            token_data = await verify_token_with_blacklist(token=token)

            # Calculate remaining TTL from the token's actual expiry claim
            remaining_ttl = max(0, int(token_data.exp - datetime.now(UTC).timestamp()))

            # Add token to blacklist
            await self.token_cache.blacklist_access_token(token=token, ttl_seconds=remaining_ttl)
            return True
        except InvalidTokenError as e:
            raise TokenValidationException() from e

    async def refresh_token(self, refresh_token: str) -> TokenSchema:
        """
        Refresh access token using refresh token.
        Args:
            refresh_token (str): Refresh token
        Returns:
            TokenSchema: New access token response
        Raises:
            TokenValidationException: If refresh token is invalid
            UserNotFoundException: If user not found
        """
        # Get user ID from refresh token
        user_id_str = await self.token_cache.get_user_from_refresh_token(token=refresh_token)
        if not user_id_str:
            raise TokenValidationException()

        # Get user from database
        user = await crud_user.get(db=self.db, id=UUID(user_id_str))
        if not user:
            raise UserNotFoundException(user_id=user_id_str)

        # Delete old refresh token
        await self.token_cache.delete_refresh_token(token=refresh_token)
        await self.token_cache.remove_user_session(user_id=user_id_str, refresh_token=refresh_token)

        # Create new tokens
        return await self.create_session_tokens(user=user)
