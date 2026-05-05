import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from ..core.models import JwtPayload
from ..core.security import verify_jwt
from ..db.db import SessionDep
from ..models.quizzes import Quiz, FullQuizResponse, QuestionResponse, BaseTestAnswer, BaseTextAnswer, QuizUpload, \
    TestAnswer, TextAnswer, Question

router = APIRouter(
    prefix="/api/quizzes",
    tags=["Quizzes"]
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

        questions.append(Question.model_validate({
            **q.model_dump(exclude={"test_answers", "text_answers"}, by_alias=True),
            "testAnswers": [ta.model_dump(by_alias=True) for ta in test_answers],
            "textAnswers": [ta.model_dump(by_alias=True) for ta in text_answers],
        }))

    quiz = Quiz.model_validate({
        **quiz_upload.model_dump(exclude={"questions"}, by_alias=True),
        "userId": jwt_payload.sub,
        "questions": [q.model_dump(by_alias=True) for q in questions],
    })
    session.add(quiz)
    session.commit()
    return prepare_quiz_response(quiz)
