import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..core.models import JwtPayload
from ..core.security import verify_jwt
from ..db.db import SessionDep
from ..models.answers import TestAnswer, TextAnswer, AnswerResponse

router = APIRouter(
    prefix="/api/answers",
    tags=["Answers"],
    responses={
        401: {"description": "JWT token is not given or expired or malformed"}
    },
)


@router.get(
    "/{answer_id}",
    response_model=AnswerResponse,
    responses={
        404: {"description": "Answer not found"},
        403: {"description": "This answer doesn't belong to you"}
    }
)
async def get_answer(
        answer_id: uuid.UUID,
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    answer: TestAnswer | None = session.exec(select(TestAnswer).where(TestAnswer.id == answer_id)).one_or_none()
    if answer is None:
        answer: TextAnswer | None = session.exec(select(TextAnswer).where(TextAnswer.id == answer_id)).one_or_none()

    if answer is None:
        raise HTTPException(404)
    if answer.question.quiz.user_id != jwt_payload.sub:
        raise HTTPException(403)

    return AnswerResponse.model_validate({
        "questionType": answer.question.type,
        "answer": {**answer.model_dump(by_alias=True, exclude={"question"})}
    })
