from datetime import datetime
from hashlib import sha256
from secrets import token_urlsafe

import jwt
from fastapi import Security
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pwdlib import PasswordHash
from pydantic import ValidationError

from . import config
from .models import JwtPayload
from ..models import user


def create_refresh_token():
    return token_urlsafe(32)


def get_refresh_token_hash(token: str):
    return sha256(token.encode(encoding="utf-8")).hexdigest()


def check_refresh_token(token: str, hashed: str):
    return get_refresh_token_hash(token) == hashed


password_hasher = PasswordHash.recommended()
auth_scheme = HTTPBearer()


def verify_password(plain: str | bytes, hashed: str | bytes) -> bool:
    return password_hasher.verify(plain, hashed)


def get_password_hash(password: str | bytes) -> str:
    return password_hasher.hash(password)


def create_access_token(user: user.User) -> str:
    now = datetime.now()
    to_encode = {
        "sub": str(user.id),
        "iat": now.timestamp(),
        "exp": (now + config.ACCESS_TOKEN_EXPIRATION).timestamp(),
    }
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(auth_scheme)) -> JwtPayload:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return JwtPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token is invalid")
    except ValidationError as e:
        raise HTTPException(status_code=401, detail=str(e))
