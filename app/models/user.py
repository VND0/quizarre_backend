import datetime
import uuid
from string import ascii_uppercase, ascii_lowercase
from uuid import uuid4, UUID

from pydantic import EmailStr, field_validator
from sqlmodel import SQLModel, Field

DIGITS = set("0123456789")
UPPERCASE_LETTERS = set(ascii_uppercase)
LOWERCASE_LETTERS = set(ascii_lowercase)


class BaseUser(SQLModel):
    email: EmailStr = Field(unique=True, max_length=254)
    name: str = Field(min_length=3, max_length=72)


class NewUser(BaseUser):
    password: str = Field(min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        chars = set(value)
        if not chars & DIGITS:
            raise ValueError("Password must contain digits")
        if not chars & LOWERCASE_LETTERS:
            raise ValueError("Password must contain lowercase latin letters")


class User(BaseUser, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    password_hash: str


class OpaqueToken(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    hash: str
    expiration: datetime.datetime
    user_id: uuid.UUID = Field(default=None, foreign_key="user.id")


class LoginUser(SQLModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(max_length=64)