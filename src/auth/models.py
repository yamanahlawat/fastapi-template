from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base_class import TimeStampedBase


class User(TimeStampedBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Password (stored as hash)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"{self.first_name} {self.last_name} <{self.email}>"
