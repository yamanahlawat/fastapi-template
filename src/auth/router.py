from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger

from src.auth.dependencies.auth import get_auth_service, get_current_user, oauth2_scheme
from src.auth.exceptions import InvalidCredentialsException, TokenValidationException
from src.auth.models import User
from src.auth.schemas.user import TokenSchema, UserResponseSchema
from src.auth.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/token",
    response_model=TokenSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "examples": {"Invalid credentials": {"value": {"detail": "Invalid email or password"}}}
                }
            },
        }
    },
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenSchema:
    """
    ## Login for Access Token

    OAuth2 compatible token login endpoint. Use your email as username.

    ### Parameters
    - **username**: User email (use email as username for OAuth2 compatibility)
    - **password**: User password

    ### Returns
    Access token that can be used for authenticating subsequent requests
    """
    try:
        return await auth_service.login(email=form_data.username, password=form_data.password)
    except InvalidCredentialsException as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


@router.get(
    "/users/me",
    response_model=UserResponseSchema,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "examples": {"Invalid token": {"value": {"detail": "Could not validate credentials"}}}
                }
            },
        }
    },
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    ## Get Current User Information

    Get information about the currently authenticated user.

    ### Returns
    Current user information
    """
    return current_user


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "examples": {"Invalid token": {"value": {"detail": "Could not validate credentials"}}}
                }
            },
        }
    },
)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    """
    ## Logout

    Logout current user by blacklisting the access token.

    ### Returns
    Success message confirming logout
    """
    try:
        await auth_service.logout(token=token)
        return {"message": "Successfully logged out"}
    except TokenValidationException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from None


@router.post(
    "/refresh",
    response_model=TokenSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid refresh token",
            "content": {
                "application/json": {"examples": {"Invalid token": {"value": {"detail": "Invalid refresh token"}}}}
            },
        }
    },
)
async def refresh_access_token(
    refresh_token: Annotated[str, Body(embed=True)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenSchema:
    """
    ## Refresh Access Token

    Get a new access token using a refresh token.

    ### Parameters
    - **refresh_token**: Valid refresh token

    ### Returns
    New access and refresh token pair
    """
    try:
        return await auth_service.refresh_token(refresh_token=refresh_token)
    except InvalidCredentialsException as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except TokenValidationException as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except Exception:
        logger.exception("Unexpected error during token refresh")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during token refresh",
        ) from None
