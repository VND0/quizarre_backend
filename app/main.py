from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import auth
from .api import users
from .db.db import create_db_and_tables


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(users.router)


@app.get(
    "/",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        },
    }
)
async def ping():
    return {"status": "ok"}
