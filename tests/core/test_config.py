from src.core.config import PostgresSettings, RedisSettings


def test_postgres_dsn_is_assembled_from_components():
    settings = PostgresSettings(HOST="db", USER="fastapi", PASSWORD="secret", DB="fastapi", PORT=5432)

    assert str(settings.DSN) == "postgresql+psycopg://fastapi:secret@db:5432/fastapi"


def test_redis_dsn_is_assembled_from_components():
    settings = RedisSettings(HOST="redis", PORT=6379, DB=0)

    assert str(settings.DSN) == "redis://redis:6379/0"
