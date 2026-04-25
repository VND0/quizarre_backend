from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship


class QuestionTypes(Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"


class Quiz(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=3, max_length=2000)

    time_to_answer: int = Field(ge=1, le=31536000)  # 31536000 is 365 days in seconds
    show_answer_immediately: bool
    require_fullscreen: bool
    shuffle_questions: bool
    encourage_speed: bool

    questions: list["Question"] = Relationship(back_populates="quiz")


class Question(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    text: str = Field(min_length=3, max_length=3000)
    description: str | None = Field(min_length=3, max_length=5000, default=None)
    type: QuestionTypes
    order_index: int = Field(le=0)
    points: float = Field(le=0)

    quiz_id: UUID | None = Field(default=None, foreign_key="quiz.id", ondelete="CASCADE")
    quiz: Quiz = Relationship(back_populates="questions")

    test_answers: list["TestAnswer"] = Relationship(back_populates="question")
    text_answers: list["TextAnswer"] = Relationship(back_populates="question")


class TestAnswer(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    text: str = Field(min_length=1, max_length=255)
    order_index: int = Field(le=0)
    is_correct: bool

    question_id: UUID | None = Field(default=None, foreign_key="question.id", ondelete="CASCADE")
    question: Question = Relationship(back_populates="test_answers")


class TextAnswer(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    text: str = Field(min_length=1, max_length=3000)

    question_id: UUID | None = Field(default=None, foreign_key="question.id", ondelete="CASCADE")
    question: Question = Relationship(back_populates="text_answers")
