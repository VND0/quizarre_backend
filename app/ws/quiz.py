import uuid
from random import sample
from string import ascii_uppercase, digits

from fastapi import APIRouter, WebSocket, HTTPException
from sqlmodel import select

from .quiz_manager import QuizFlow
from ..core.security import get_jwt_payload
from ..db.db import SessionDep
from ..models.quizzes import Quiz

router = APIRouter(prefix="/ws")
quizzes: dict[str, QuizFlow] = {}


def get_quiz_code() -> str:
    charset = ascii_uppercase + digits
    existing_codes = quizzes.keys()

    while True:
        new_code = "".join(sample(charset, 6))
        if new_code not in existing_codes:
            break

    return new_code


@router.websocket("/run-quiz")
async def run_quiz(
        websocket: WebSocket,
        quiz_id: uuid.UUID,
        session: SessionDep
):
    subprotocols = websocket.scope["subprotocols"]
    if len(subprotocols) < 2 or subprotocols[0] != "Authorization":
        raise HTTPException(401, "JWT token required")
    token = subprotocols[1].lstrip("Bearer ")
    jwt_payload = get_jwt_payload(token)

    quiz: Quiz | None = session.exec(select(Quiz).where(Quiz.id == quiz_id)).one_or_none()
    if quiz is None:
        raise HTTPException(404, "Quiz not found")
    if quiz.user_id != jwt_payload.sub:
        raise HTTPException(403, "This quiz doesn't belong to you")

    await websocket.accept()
    quiz_flow = QuizFlow(quiz=quiz, admin=websocket)
    code = get_quiz_code()
    quizzes[code] = quiz_flow
    await quiz_flow.handle_admin_requests()


@router.websocket("/join-quiz")
async def join_quiz(
        websocket: WebSocket,
        join_str: str,
):
    pass
