from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User


class QuestionTypes(Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"


class BaseQuiz(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=3, max_length=2000)

    time_to_answer: int = Field(ge=1, le=31536000, alias="timeToAnswer")  # 31536000 is 365 days in seconds
    show_answer_immediately: bool = Field(alias="showAnswerImmediately")
    require_fullscreen: bool = Field(alias="requireFullscreen")
    shuffle_questions: bool = Field(alias="shuffleQuestions")
    encourage_speed: bool = Field(alias="encourageSpeed")

    user_id: UUID | None = Field(default=None, foreign_key="user.id", ondelete="CASCADE", alias="userId")


class Quiz(BaseQuiz, table=True):
    user: "User" = Relationship(back_populates="quizzes")
    questions: list["Question"] = Relationship(back_populates="quiz")


class BaseQuestion(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    text: str = Field(min_length=3, max_length=3000)
    description: str | None = Field(min_length=3, max_length=5000, default=None)
    type: QuestionTypes
    order_index: int = Field(le=0, alias="orderIndex")
    points: float = Field(le=0)

    quiz_id: UUID | None = Field(default=None, foreign_key="quiz.id", ondelete="CASCADE", alias="quizId")


class Question(BaseQuestion, table=True):
    quiz: Quiz = Relationship(back_populates="questions")

    test_answers: list["TestAnswer"] = Relationship(back_populates="question")
    text_answers: list["TextAnswer"] = Relationship(back_populates="question")


class BaseTestAnswer(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    text: str = Field(min_length=1, max_length=255)
    order_index: int = Field(le=0, alias="orderIndex")
    is_correct: bool = Field(alias="isCorrect")

    question_id: UUID | None = Field(default=None, foreign_key="question.id", ondelete="CASCADE", alias="questionId")


class TestAnswer(BaseTestAnswer, table=True):
    question: Question = Relationship(back_populates="test_answers")


class BaseTextAnswer(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    text: str = Field(min_length=1, max_length=3000)

    question_id: UUID | None = Field(default=None, foreign_key="question.id", ondelete="CASCADE", alias="questionId")


class TextAnswer(BaseTextAnswer, table=True):
    question: Question = Relationship(back_populates="text_answers")


class QuestionResponse(BaseQuestion):
    test_answers: list[BaseTestAnswer] = Field(alias="testAnswers")
    text_answers: list[BaseTextAnswer] = Field(alias="textAnswers")


class FullQuizResponse(BaseQuiz):
    questions: list[QuestionResponse]
