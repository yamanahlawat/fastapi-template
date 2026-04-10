from collections.abc import Sequence
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from src.database.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase[ModelType: Base, CreateSchemaType: BaseModel, UpdateSchemaType: BaseModel]:
    """
    Base class for CRUD operations: create, read, update, delete.
    It's meant to be extended by specific model CRUD classes,
    providing basic CRUD operations for a given SQLAlchemy model.
    """

    def __init__(self, model: type[ModelType]) -> None:
        """
        Initialize the CRUDBase class with the model type.
        Args:
            model (Type[ModelType]): SQLAlchemy model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> ModelType | None:
        """
        Get a specific record by id.
        Args:
            db (AsyncSession): Database session
            id (UUID): Id of the record to fetch
        Returns:
            Instance of the ModelType if found, else None
        """
        return await db.get(self.model, id)

    async def filter(
        self,
        db: AsyncSession,
        *,
        order_on: list[InstrumentedAttribute] | None = None,
        offset: int = 0,
        limit: int = 10,
        filters: list[InstrumentedAttribute] | None = None,
    ) -> Sequence[ModelType]:
        """
        Get multiple records from the database based on the provided filters and
        pagination parameters.
        Args:
            db (AsyncSession): Database session
            order_on (list[InstrumentedAttribute] | None, optional): Ordering of records. Defaults to None.
            offset (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to retrieve. Defaults to 10.
            filters (list[InstrumentedAttribute] | None, optional): Filters to apply. Defaults to None.
        Returns:
            Sequence[ModelType]: List of instances of the ModelType
        """
        if order_on is None:
            # Default ordering by model's ID
            order_on = [desc(self.model.created_at)]  # type: ignore

        # Start query
        query = select(self.model)
        if filters:
            query = query.where(*filters)
        query = query.order_by(*order_on).offset(offset).limit(limit)  # type: ignore
        items = await db.scalars(query)
        return items.all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record with provided input data.
        Args:
            db (AsyncSession): Database session
            obj_in (CreateSchemaType): Pydantic schema model with the data to create a new record
        Returns:
            Instance of the ModelType for the created record
        """
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(instance=db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, id: Any, obj_in: UpdateSchemaType) -> ModelType | None:
        """
        Update a specific record by id.
        Args:
            db (AsyncSession): Database session
            id (Any): Id of the record to update
            obj_in (UpdateSchemaType): Pydantic schema model with the data to update
        Returns:
            ModelType | None: Instance of the ModelType for the updated record if found, else None
        """
        db_obj = await db.get(self.model, id)
        if not db_obj:
            return None

        obj_in_data = obj_in.model_dump(mode="json", exclude_unset=True)
        for field, value in obj_in_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: UUID) -> None:
        """
        Delete a specific record by id.
        Args:
            db (AsyncSession): Database session
            id (UUID): Id of the record to delete
        """
        db_obj = await db.get(self.model, id)
        if not db_obj:
            return
        await db.delete(db_obj)
        await db.commit()
