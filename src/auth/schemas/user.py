from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBaseSchema(BaseModel):
    """Base user schema"""

    email: EmailStr
    first_name: str
    last_name: str


class UserResponseSchema(UserBaseSchema):
    """User response schema"""

    id: UUID
    model_config = ConfigDict(from_attributes=True)


class TokenDataSchema(BaseModel):
    """JWT token data schema"""

    user_id: UUID
    exp: int


class TokenSchema(BaseModel):
    """Access token response schema"""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
