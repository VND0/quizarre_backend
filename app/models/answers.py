from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .questions import Question


class TestAnswerData(SQLModel):
    text: str = Field(min_length=1, max_length=255)
    order_index: int = Field(ge=0, alias="orderIndex")
    is_correct: bool = Field(alias="isCorrect")


class BaseTestAnswer(TestAnswerData):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    question_id: UUID | None = Field(default=None, foreign_key="question.id", ondelete="CASCADE", alias="questionId")


class TestAnswer(BaseTestAnswer, table=True):
    question: Question = Relationship(back_populates="test_answers")


class TextAnswerData(SQLModel):
    text: str = Field(min_length=1, max_length=3000)


class BaseTextAnswer(TextAnswerData):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    question_id: UUID | None = Field(default=None, foreign_key="question.id", ondelete="CASCADE", alias="questionId")


class TextAnswer(BaseTextAnswer, table=True):
    question: Question = Relationship(back_populates="text_answers")