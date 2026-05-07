import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..core.models import JwtPayload
from ..core.security import verify_jwt
from ..core.utils import validate_answers
from ..db.db import SessionDep
from ..models.answers import TestAnswer, TextAnswer, AnswerResponse, TestAnswerData, TextAnswerData
from ..models.questions import Question

router = APIRouter(
    prefix="/api/answers",
    tags=["Answers"],
    responses={
        401: {"description": "JWT token is not given or expired or malformed"},
        404: {"description": "Object not found"},
        403: {"description": "This object doesn't belong to you"},
        400: {"description": "This change breaks validity of the question. Parse the body to get the details"}
    },
)


@router.get("/{answer_id}", response_model=AnswerResponse)
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


def get_question(question_id: uuid.UUID, session: SessionDep, jwt_payload: JwtPayload):
    question: Question | None = session.exec(select(Question).where(Question.id == question_id)).one_or_none()
    if question is None:
        raise HTTPException(404)
    if question.quiz.user_id != jwt_payload.sub:
        raise HTTPException(403)
    return question


@router.post("/new-test/{question_id}", response_model=AnswerResponse)
async def add_test_answer(
        question_id: uuid.UUID,
        session: SessionDep,
        answer_data: TestAnswerData,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    question = get_question(question_id, session, jwt_payload)
    new_answer = TestAnswer.model_validate({**answer_data.model_dump(by_alias=True)})
    question.test_answers.append(new_answer)

    try:
        validate_answers(question)
    except ValueError as e:
        raise HTTPException(400, str(e))

    session.commit()
    session.refresh(new_answer)
    return AnswerResponse.model_validate({
        "questionType": question.type,
        "answer": {**new_answer.model_dump(by_alias=True, exclude={"question"})}
    })


@router.post("/new-text/{question_id}", response_model=AnswerResponse)
async def add_text_answer(
        question_id: uuid.UUID,
        session: SessionDep,
        answer_data: TextAnswerData,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    question = get_question(question_id, session, jwt_payload)
    new_answer = TextAnswer.model_validate({**answer_data.model_dump(by_alias=True)})
    question.text_answers.append(new_answer)

    try:
        validate_answers(question)
    except ValueError as e:
        raise HTTPException(400, str(e))

    session.commit()
    return AnswerResponse.model_validate({
        "questionType": question.type,
        "answer": {**new_answer.model_dump(by_alias=True, exclude={"question"})}
    })