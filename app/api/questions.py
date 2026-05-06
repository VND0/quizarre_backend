import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..core.models import JwtPayload
from ..core.security import verify_jwt
from ..db.db import SessionDep
from ..models.questions import Question, QuestionResponse
from ..models.quizzes import Quiz

router = APIRouter(
    prefix="/api/questions",
    tags=["Questions"],
    responses={
        401: {"description": "JWT token is not given or expired or malformed"}
    },
)


@router.get(
    "",
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


def prepare_question_response(question: Question) -> QuestionResponse:
    test_answers = [ta.model_dump(by_alias=True) for ta in question.test_answers]
    text_answers = [ta.model_dump(by_alias=True) for ta in question.text_answers]

    return QuestionResponse.model_validate({
        **question.model_dump(by_alias=True),
        "testAnswers": test_answers,
        "textAnswers": text_answers,
    })


@router.get(
    "/{question_id}",
    response_model=QuestionResponse
)
async def get_question(
        question_id: uuid.UUID,
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    question: Question | None = session.exec(select(Question).where(Question.id == question_id)).one_or_none()
    if question is None:
        raise HTTPException(404)
    if question.quiz.user_id != jwt_payload.sub:
        raise HTTPException(403)

    return prepare_question_response(question)
