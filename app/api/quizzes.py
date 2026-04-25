from fastapi import APIRouter, Depends
from sqlmodel import select

from ..core.models import JwtPayload
from ..core.security import verify_jwt
from ..db.db import SessionDep
from ..models.quizzes import Quiz, FullQuizResponse

router = APIRouter(
    prefix="/api/quizzes",
    tags=["Quizzes"]
)


@router.get("", response_model=list[Quiz])
async def get_quizzes(
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt)
):
    return session.exec(select(Quiz).where(Quiz.user_id == jwt_payload.sub)).all()


@router.get("/{quiz_id}", response_model=FullQuizResponse)
async def get_quiz_data(
        session: SessionDep,
        quiz_id: str,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    quiz = session.exec(select(Quiz).where(Quiz.id == quiz_id)).one_or_none()
    if quiz is None
