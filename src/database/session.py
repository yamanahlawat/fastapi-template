from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import settings

async_engine = create_async_engine(
    url=str(settings.POSTGRES.DSN),
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(bind=async_engine, autocommit=False, autoflush=False, expire_on_commit=False)
