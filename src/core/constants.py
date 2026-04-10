from enum import StrEnum
from typing import Any


class BaseEnum(StrEnum):
    @classmethod
    def values(cls) -> list[Any]:
        """Returns all enum member values as a plain list."""
        return [item.value for item in cls]


class Environment(BaseEnum):
    """
    An enumeration representing the various environments in which the application can run.
    Attributes:
        LOCAL: Represents a local development environment on a developer's machine.
        DEVELOPMENT: Represents a shared development environment, often used for testing and staging.
        PRODUCTION: Represents the final environment where the application is available to end users.
    """

    LOCAL = "local"
    DEVELOPMENT = "development"
    PRODUCTION = "production"
