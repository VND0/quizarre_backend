from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.db import create_db_and_tables
from .core import config
from .api import quizzes, questions, auth, users, answers


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(quizzes.router)
app.include_router(questions.router)
app.include_router(answers.router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=config.CORS_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
