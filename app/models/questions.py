from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship

from .answers import TestAnswer, TextAnswer, BaseTestAnswer, BaseTextAnswer, TestAnswerData, TextAnswerData

if TYPE_CHECKING:
    from .quizzes import Quiz


class QuestionTypes(Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"


class QuestionData(SQLModel):
    text: str = Field(min_length=3, max_length=3000)
    description: str | None = Field(min_length=3, max_length=5000, default=None)
    type: QuestionTypes
    order_index: int = Field(ge=0, alias="orderIndex")
    points: float = Field(ge=0)


class BaseQuestion(QuestionData):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quiz_id: UUID | None = Field(default=None, foreign_key="quiz.id", ondelete="CASCADE", alias="quizId")


class Question(BaseQuestion, table=True):
    quiz: Quiz = Relationship(back_populates="questions")

    test_answers: list["TestAnswer"] = Relationship(back_populates="question")
    text_answers: list["TextAnswer"] = Relationship(back_populates="question")


class QuestionResponse(BaseQuestion):
    test_answers: list[BaseTestAnswer] = Field(alias="testAnswers")
    text_answers: list[BaseTextAnswer] = Field(alias="textAnswers")


class QuestionUpload(QuestionData):
    test_answers: list[TestAnswerData] = Field(alias="testAnswers")
    text_answers: list[TextAnswerData] = Field(alias="textAnswers")
