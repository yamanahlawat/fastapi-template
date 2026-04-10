from functools import lru_cache

from pydantic import (
    HttpUrl,
    PostgresDsn,
    RedisDsn,
    SecretStr,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.constants import Environment


class PostgresSettings(BaseSettings):
    # Postgres database URI
    HOST: str
    USER: str
    PASSWORD: SecretStr
    DB: str
    PORT: int = 5432
    DSN: PostgresDsn | None = None

    @field_validator("DSN", mode="after")
    @classmethod
    def assemble_db_connection_uri(cls, value: PostgresDsn | None, info: ValidationInfo) -> PostgresDsn:
        """
        Assembles the database connection URI from the individual components.
        """
        if isinstance(value, str):
            return value
        values = info.data
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=values.get("USER"),
            password=values.get("PASSWORD").get_secret_value(),  # type: ignore
            host=values.get("HOST"),
            port=values.get("PORT"),
            path=values.get("DB"),
        )


class RedisSettings(BaseSettings):
    """
    Settings for Redis connection.
    """

    HOST: str
    PORT: int = 6379
    DB: int = 0
    DSN: RedisDsn | None = None

    @field_validator("DSN", mode="after")
    def assemble_redis_connection_uri(cls, value: RedisDsn | None, info: ValidationInfo) -> RedisDsn:
        """
        Assembles the Redis connection URI from the individual components.
        """
        if isinstance(value, str):
            return value
        values = info.data
        return RedisDsn.build(
            scheme="redis",
            host=values.get("HOST", ""),
            port=values.get("PORT"),
            path=str(values.get("DB")),
        )


class Settings(BaseSettings):
    """Application settings for FastAPI template."""

    PROJECT_NAME: str = "FastAPI Template"
    PROJECT_DESCRIPTION: str = "A FastAPI template with authentication and database integration"

    # the route for api docs and all endpoints
    API_URL: str = "/api"

    # The current environment
    ENVIRONMENT: Environment = Environment.LOCAL

    # List of allowed CORS origins
    ALLOWED_CORS_ORIGINS: list[HttpUrl] = []

    # JWT
    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    POSTGRES: PostgresSettings
    REDIS: RedisSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Retrieves and caches the application settings.
    """
    return Settings()  # type: ignore


settings = get_settings()
