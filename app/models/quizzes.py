from typing import TYPE_CHECKING, Self
from uuid import UUID, uuid4

from pydantic import model_validator
from sqlmodel import SQLModel, Field, Relationship

from .questions import Question, QuestionResponse, QuestionUpload
from ..core.utils import validate_questions_indexes

if TYPE_CHECKING:
    from .user import User


class QuizData(SQLModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=3, max_length=2000)

    time_to_answer: int = Field(ge=1, le=31536000, alias="timeToAnswer",  # 31536000 is 365 days in seconds
                                description="Time to answer each question in seconds")
    show_answer_immediately: bool = Field(alias="showAnswerImmediately",
                                          description="If true, user will see the correct option right after he answered.")
    require_fullscreen: bool = Field(alias="requireFullscreen",
                                     description="If true, user must enter fullscreen mode to play")
    shuffle_questions: bool = Field(alias="shuffleQuestions")
    encourage_speed: bool = Field(alias="encourageSpeed",
                                  description="If true, user will have higher scores for the answers (up to 1.5x).")


class BaseQuiz(QuizData):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID | None = Field(default=None, foreign_key="user.id", ondelete="CASCADE", alias="userId")


class Quiz(BaseQuiz, table=True):
    user: "User" = Relationship(back_populates="quizzes")
    questions: list["Question"] = Relationship(back_populates="quiz")


class FullQuizResponse(BaseQuiz):
    questions: list[QuestionResponse]


class QuizUpload(QuizData):
    questions: list[QuestionUpload]

    @model_validator(mode="after")
    def validate_quiz(self) -> Self:
        validate_questions_indexes(self)
        return self
