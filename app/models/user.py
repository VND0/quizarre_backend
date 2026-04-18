import datetime
import uuid
from string import ascii_uppercase, ascii_lowercase
from typing import Annotated
from uuid import uuid4, UUID

from pydantic import EmailStr, AfterValidator
from sqlmodel import SQLModel, Field

DIGITS = set("0123456789")
UPPERCASE_LETTERS = set(ascii_uppercase)
LOWERCASE_LETTERS = set(ascii_lowercase)


def validate_password(value: str):
    chars = set(value)
    if not chars & DIGITS:
        raise ValueError("Password must contain digits")
    if not chars & LOWERCASE_LETTERS:
        raise ValueError("Password must contain lowercase latin letters")
    return value


class BaseUser(SQLModel):
    email: EmailStr = Field(unique=True, max_length=254)
    name: str = Field(min_length=3, max_length=72)


class NewUser(BaseUser):
    password: Annotated[str, AfterValidator(validate_password)] = Field(min_length=8, max_length=64)


class User(BaseUser, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    password_hash: str = Field(exclude=True)


class OpaqueToken(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    hash: str
    expiration: datetime.datetime
    user_id: uuid.UUID = Field(default=None, foreign_key="user.id")


class LoginUser(SQLModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=8, max_length=64)


class NewTokens(SQLModel):
    access_token: str | None = Field(alias="accessToken", default=None)
    refresh_token: str | None = Field(alias="refreshToken", default=None)


class UserResponse(SQLModel):
    user: User
    tokens: NewTokens


class UserPatch(SQLModel):
    email: EmailStr | None = Field(max_length=254, default=None)
    name: str | None = Field(min_length=3, max_length=72, default=None)
    password: Annotated[str, AfterValidator(validate_password)] | None = Field(min_length=8, max_length=64,
                                                                               default=None)


class ExistingRefreshToken(SQLModel):
    token: str
