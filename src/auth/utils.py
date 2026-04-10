import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from jwt.exceptions import InvalidTokenError

from src.auth.schemas.user import TokenDataSchema
from src.auth.services.token_cache import TokenCacheService
from src.core.config import settings

# Password hashing with Argon2id (OWASP recommended)
password_hasher = PasswordHasher()
token_cache_service = TokenCacheService()

# Pre-computed dummy hash for timing attack prevention.
# When a login attempt is made for a non-existent user, we still run
# password verification against this hash so the response time is
# indistinguishable from a real user lookup.
DUMMY_PASSWORD_HASH: str = password_hasher.hash(secrets.token_hex(32))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against the hashed password using Argon2.
    Args:
        plain_password (str): The plain text password
        hashed_password (str): The hashed password to verify against
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        password_hasher.verify(hash=hashed_password, password=plain_password)
        return True
    except VerifyMismatchError, InvalidHashError:
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2id.
    Args:
        password (str): The plain text password to hash
    Returns:
        str: The hashed password
    """
    return password_hasher.hash(password=password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.
    Args:
        data (dict): The data to encode in the token
        expires_delta (timedelta, optional): Token expiration time
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    issued_at = datetime.now(UTC)

    # Generate a unique token ID
    jti = uuid4().hex

    expire = issued_at + expires_delta if expires_delta else issued_at + timedelta(minutes=15)

    to_encode.update({"iat": issued_at, "exp": expire, "jti": jti})

    return jwt.encode(
        payload=to_encode, key=settings.JWT_SECRET_KEY.get_secret_value(), algorithm=settings.JWT_ALGORITHM
    )


def verify_token(token: str) -> TokenDataSchema:
    """
    Verify and decode a JWT token.
    Args:
        token (str): The JWT token to verify
    Returns:
        TokenDataSchema: The decoded token data
    Raises:
        InvalidTokenError: If token is invalid or expired
    """
    payload = jwt.decode(
        jwt=token,
        key=settings.JWT_SECRET_KEY.get_secret_value(),
        algorithms=[settings.JWT_ALGORITHM],
    )

    user_id = payload.get("sub")
    exp = payload.get("exp")

    if user_id is None:
        raise InvalidTokenError("Token missing user ID")

    if exp is None:
        raise InvalidTokenError("Token missing expiry")

    return TokenDataSchema(user_id=user_id, exp=exp)


def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure refresh token.

    Returns:
        str: A secure random token string
    """
    return secrets.token_urlsafe(64)


async def verify_token_with_blacklist(token: str) -> TokenDataSchema:
    """
    Verify JWT token and check Redis blacklist.

    Args:
        token: JWT token to verify

    Returns:
        TokenDataSchema: Decoded token data

    Raises:
        InvalidTokenError: If token is invalid, expired, or blacklisted
    """
    # First verify the token cryptographically
    token_data = verify_token(token=token)

    # Check if token is blacklisted in Redis
    if await token_cache_service.is_token_blacklisted(token=token):
        raise InvalidTokenError("Token has been revoked")

    return token_data


def needs_hashing(password: str) -> bool:
    """
    Check if the password needs hashing.

    Args:
        password (str): The password to check

    Returns:
        bool: True if password needs hashing, False if it is already hashed
    """
    try:
        return password_hasher.check_needs_rehash(hash=password)
    except InvalidHashError:
        return True
