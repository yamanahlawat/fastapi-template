from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """
    Returns an async generator object that provides an asynchronous database session.
    """
    async with AsyncSessionLocal() as database_session:
        yield database_session
