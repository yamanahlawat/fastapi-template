from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.database.crud_base import CreateSchemaType, CRUDBase, UpdateSchemaType


class CRUDUser(CRUDBase[User, CreateSchemaType, UpdateSchemaType]):
    """
    CRUD operations for User model.
    """

    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        """
        Get user by email.
        Args:
            db (AsyncSession): Database session
            email (str): User email
        Returns:
            User | None: User object if found, None otherwise
        """
        statement = select(self.model).where(self.model.email == email)
        result = await db.execute(statement)
        return result.scalar_one_or_none()


# Create instance of CRUD operations
crud_user = CRUDUser(User)
