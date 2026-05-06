import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..core.models import JwtPayload
from ..core.security import verify_jwt
from ..db.db import SessionDep
from ..models.questions import Question
from ..models.quizzes import Quiz

router = APIRouter(
    prefix="/api/questions",
    tags=["Questions"],
    responses={
        401: {"description": "JWT token is not given or expired or malformed"}
    },
)


@router.get(
    "/{quiz_id}",
    response_model=list[Question],
    responses={
        404: {"description": "Quiz not found"},
        403: {"description": "This quiz doesn't belong to you"}
    }
)
async def get_questions(
        quiz_id: uuid.UUID,
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt)
):
    quiz: Quiz | None = session.exec(select(Quiz).where(Quiz.id == quiz_id)).one_or_none()
    if quiz is None:
        raise HTTPException(404)
    if quiz.user_id != jwt_payload.sub:
        raise HTTPException(403)

    return quiz.questions
