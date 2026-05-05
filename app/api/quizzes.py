import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..core.models import JwtPayload
from ..core.security import verify_jwt
from ..db.db import SessionDep
from ..models.answers import BaseTestAnswer, BaseTextAnswer, TestAnswer, TextAnswer
from ..models.questions import QuestionResponse, Question
from ..models.quizzes import Quiz, FullQuizResponse, QuizUpload, QuizData

router = APIRouter(
    prefix="/api/quizzes",
    tags=["Quizzes"],
    responses={
        401: {"description": "JWT token is not given or expired or malformed"}
    }
)


def prepare_quiz_response(quiz: Quiz) -> FullQuizResponse:
    questions = []
    for q in quiz.questions:
        test_answers = []
        for ta in q.test_answers:
            test_answers.append(BaseTestAnswer.model_validate({**ta.model_dump(by_alias=True)}))

        text_answer = []
        for ta in q.text_answers:
            text_answer.append(BaseTextAnswer.model_validate({**ta.model_dump(by_alias=True)}))

        questions.append(QuestionResponse.model_validate({
            **q.model_dump(exclude={"test_answers", "text_answers"}, by_alias=True),
            "testAnswers": [ta.model_dump(by_alias=True) for ta in test_answers],
            "textAnswers": [ta.model_dump(by_alias=True) for ta in text_answer],
        }))

    return FullQuizResponse.model_validate({
        **quiz.model_dump(by_alias=True),
        "questions": [q.model_dump(by_alias=True) for q in questions]
    })


@router.get("", response_model=list[Quiz])
async def get_quizzes(
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt)
):
    return session.exec(select(Quiz).where(Quiz.user_id == jwt_payload.sub)).all()


@router.get(
    "/{quiz_id}",
    response_model=FullQuizResponse,
    responses={
        404: {"description": "Quiz not found"},
        403: {"description": "This quiz doesn't belong to you"}
    }
)
async def get_quiz_data(
        session: SessionDep,
        quiz_id: uuid.UUID,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    quiz: Quiz | None = session.exec(select(Quiz).where(Quiz.id == quiz_id)).one_or_none()
    if quiz is None:
        raise HTTPException(404)
    if quiz.user_id != jwt_payload.sub:
        raise HTTPException(403)

    return prepare_quiz_response(quiz)


@router.post("", response_model=FullQuizResponse)
async def upload_quiz(
        session: SessionDep,
        quiz_upload: QuizUpload,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    questions = []
    for q in quiz_upload.questions:
        test_answers = []
        text_answers = []

        for ta in q.test_answers:
            test_answers.append(TestAnswer.model_validate({**ta.model_dump(by_alias=True)}))
        for ta in q.text_answers:
            text_answers.append(TextAnswer.model_validate({**ta.model_dump(by_alias=True)}))

        new_question = Question.model_validate({
            **q.model_dump(exclude={"test_answers", "text_answers"}, by_alias=True),
            "testAnswers": [],
            "textAnswers": [],
        })
        new_question.test_answers.extend(
            [TestAnswer.model_validate(ta.model_dump(by_alias=True)) for ta in test_answers]
        )
        new_question.text_answers.extend(
            [TextAnswer.model_validate(ta.model_dump(by_alias=True)) for ta in text_answers]
        )
        questions.append(new_question)

    quiz = Quiz.model_validate({
        **quiz_upload.model_dump(exclude={"questions"}, by_alias=True),
        "userId": jwt_payload.sub,
        "questions": [],
    })
    quiz.questions.extend(questions)
    session.add(quiz)
    session.commit()
    return prepare_quiz_response(quiz)


@router.put(
    "/{quiz_id}",
    response_model=FullQuizResponse,
    responses={
        404: {"description": "Quiz not found"},
        403: {"description": "This quiz doesn't belong to you"}
    }
)
async def update_quiz_data(
        quiz_id: uuid.UUID,
        quiz_data: QuizData,
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    quiz: Quiz | None = session.exec(select(Quiz).where(Quiz.id == quiz_id)).one_or_none()
    if quiz is None:
        raise HTTPException(404)
    if quiz.user_id != jwt_payload.sub:
        raise HTTPException(403)

    quiz.sqlmodel_update(quiz_data)
    session.commit()
    return prepare_quiz_response(quiz)


@router.delete(
    "/{quiz_id}",
    response_model=FullQuizResponse,
)
async def delete_quiz(
        quiz_id: uuid.UUID,
        session: SessionDep,
        jwt_payload: JwtPayload = Depends(verify_jwt),
):
    quiz: Quiz | None = session.exec(select(Quiz).where(Quiz.id == quiz_id)).one_or_none()
    if quiz is None:
        raise HTTPException(404)
    if quiz.user_id != jwt_payload.sub:
        raise HTTPException(403)

    response = prepare_quiz_response(quiz)
    session.delete(quiz)
    session.commit()
    return response
