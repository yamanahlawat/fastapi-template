from typing import Annotated

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import TokenValidationException, UserNotFoundException
from src.auth.models import User
from src.auth.services.auth import AuthService
from src.database.dependencies import get_db_session

# OAuth2 scheme for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

INVALID_TOKEN_OR_EXPIRED = "Could not validate credentials"


def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthService:
    """
    Get auth service dependency.
    Args:
        db: Database session
    Returns:
        AuthService: Auth service instance
    """
    return AuthService(db=db)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """
    Get current user from JWT token with revocation checking.
    Args:
        token (str): JWT token from OAuth2 scheme
        auth_service (AuthService): Auth service instance
    Returns:
        User: Current authenticated user
    Raises:
        HTTPException: If token is invalid, revoked, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_TOKEN_OR_EXPIRED,
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        return await auth_service.get_current_user(token=token)
    except TokenValidationException, UserNotFoundException:
        raise credentials_exception from None
