import os
from datetime import timedelta


def get_env_variable(name: str):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Value by the name '{name}' is either unset or empty")
    return value


SQLITE_FILE_NAME = get_env_variable("SQLITE_FILE_NAME")
SECRET_KEY = get_env_variable("SECRET_KEY")
CORS_ALLOWED_ORIGINS = get_env_variable("CORS_ALLOWED_ORIGINS")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION = timedelta(minutes=30)
REFRESH_TOKEN_EXPIRATION = timedelta(days=1) * 30

