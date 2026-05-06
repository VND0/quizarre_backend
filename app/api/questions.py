import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..core.models import JwtPayload
from ..core.security import verify_jwt
from ..core.utils import validate_questions_indexes, validate_answers
from ..db.db import SessionDep
from ..models.questions import Question, QuestionResponse, QuestionData, QuestionUpload
from ..models.quizzes import Quiz
from ..models.answers import TestAnswer, TextAnswer

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
    response_model=QuestionResponse,
    responses={
        404: {"description": "Question not found"},
        403: {"description": "This question doesn't belong to you"}
    }
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


@router.put(
    "/{question_id}",
    response_model=QuestionResponse,
    responses={
        404: {"description": "Question not found"},
        403: {"description": "This question doesn't belong to you"},
        400: {"description": "Bad request. Parse body to get more information"},
    }
)
async def edit_question_data(
        question_id: uuid.UUID,
        session: SessionDep,
        update_data: QuestionData,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    question: Question | None = session.exec(select(Question).where(Question.id == question_id)).one_or_none()
    if question is None:
        raise HTTPException(404)
    if question.quiz.user_id != jwt_payload.sub:
        raise HTTPException(403)

    question.sqlmodel_update(update_data)

    try:
        validate_questions_indexes(question.quiz)
    except ValueError as e:
        raise HTTPException(400, str(e))

    session.commit()
    return prepare_question_response(question)


@router.delete(
    "/{question_id}",
    response_model=QuestionResponse,
    responses={
        404: {"description": "Question not found"},
        403: {"description": "This question doesn't belong to you"}
    }
)
async def delete_question(
        question_id: uuid.UUID,
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    question: Question | None = session.exec(select(Question).where(Question.id == question_id)).one_or_none()
    if question is None:
        raise HTTPException(404)
    if question.quiz.user_id != jwt_payload.sub:
        raise HTTPException(403)

    response = prepare_question_response(question)
    session.delete(question)
    session.commit()
    return response


@router.post(
    "",
    response_model=QuestionResponse,
    responses={
        404: {"description": "Quiz not found"},
        403: {"description": "This quiz doesn't belong to you"},
        400: {"description": "Bad request. Parse body to get more information"},
    },
)
async def add_question(
        quiz_id: uuid.UUID,
        question_upload: QuestionUpload,
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    quiz: Quiz | None = session.exec(select(Quiz).where(Quiz.id == quiz_id)).one_or_none()
    if quiz is None:
        raise HTTPException(404)
    if quiz.user_id != jwt_payload.sub:
        raise HTTPException(403)

    test_answers = []
    text_answers = []

    for ta in question_upload.test_answers:
        test_answers.append(TestAnswer.model_validate({**ta.model_dump(by_alias=True)}))
    for ta in question_upload.text_answers:
        text_answers.append(TextAnswer.model_validate({**ta.model_dump(by_alias=True)}))

    new_question = Question.model_validate({
        **question_upload.model_dump(exclude={"test_answers", "text_answers"}, by_alias=True),
        "testAnswers": [],
        "textAnswers": [],
    })
    new_question.test_answers.extend(
        [TestAnswer.model_validate(ta.model_dump(by_alias=True)) for ta in test_answers]
    )
    new_question.text_answers.extend(
        [TextAnswer.model_validate(ta.model_dump(by_alias=True)) for ta in text_answers]
    )

    try:
        validate_answers(new_question)
        quiz.questions.append(new_question)
        validate_questions_indexes(quiz)
    except ValueError as e:
        raise HTTPException(400, str(e))

    session.commit()
    session.refresh(new_question)
    return prepare_question_response(new_question)
