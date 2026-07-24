"""Unit tests for AuthService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.auth.exceptions import InvalidCredentialsException
from src.auth.services.auth import AuthService
from src.auth.utils import get_password_hash


class TestAuthenticateUser:
    """Tests for AuthService.authenticate_user."""

    def make_user(self, *, password_hash: str) -> MagicMock:
        user = MagicMock()
        user.id = "11111111-1111-1111-1111-111111111111"
        user.email = "person@example.com"
        user.password = password_hash
        return user

    async def test_valid_credentials_returns_user(self, mock_db):
        password_hash = get_password_hash("correct-horse-battery-staple")
        user = self.make_user(password_hash=password_hash)

        with patch("src.auth.services.auth.crud_user") as mock_crud_user:
            mock_crud_user.get_by_email = AsyncMock(return_value=user)
            service = AuthService(db=mock_db)
            result = await service.authenticate_user(email=user.email, password="correct-horse-battery-staple")

        assert result is user
        mock_crud_user.get_by_email.assert_awaited_once_with(db=mock_db, email=user.email)

    async def test_wrong_password_raises_invalid_credentials(self, mock_db):
        user = self.make_user(password_hash=get_password_hash("the-real-password"))

        with patch("src.auth.services.auth.crud_user") as mock_crud_user:
            mock_crud_user.get_by_email = AsyncMock(return_value=user)
            service = AuthService(db=mock_db)
            with pytest.raises(InvalidCredentialsException, match="Invalid email or password"):
                await service.authenticate_user(email=user.email, password="wrong-password")

    async def test_unknown_user_raises_invalid_credentials(self, mock_db):
        with patch("src.auth.services.auth.crud_user") as mock_crud_user:
            mock_crud_user.get_by_email = AsyncMock(return_value=None)
            service = AuthService(db=mock_db)
            with pytest.raises(InvalidCredentialsException, match="Invalid email or password"):
                await service.authenticate_user(email="nobody@example.com", password="anything")


class TestLogin:
    """Tests for AuthService.login."""

    async def test_login_returns_tokens_for_valid_credentials(self, mock_db):
        user = MagicMock()
        user.id = "11111111-1111-1111-1111-111111111111"
        user.password = get_password_hash("correct-horse-battery-staple")

        with (
            patch("src.auth.services.auth.crud_user") as mock_crud_user,
            patch("src.auth.services.auth.TokenCacheService") as mock_token_cache_cls,
        ):
            mock_crud_user.get_by_email = AsyncMock(return_value=user)
            mock_token_cache = mock_token_cache_cls.return_value
            mock_token_cache.store_refresh_token = AsyncMock(return_value=True)
            mock_token_cache.add_user_session = AsyncMock(return_value=True)

            service = AuthService(db=mock_db)
            token = await service.login(email="person@example.com", password="correct-horse-battery-staple")

        assert token.token_type == "bearer"
        assert token.access_token
        assert token.refresh_token
        mock_token_cache.store_refresh_token.assert_awaited_once()
        mock_token_cache.add_user_session.assert_awaited_once()
