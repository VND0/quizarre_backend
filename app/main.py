from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db.db import create_db_and_tables
from .api import auth


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)

@app.get("/")
async def index():
    return {"status": "ok"}
