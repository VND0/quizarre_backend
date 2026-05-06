from enum import Enum
from typing import TYPE_CHECKING, Self
from uuid import UUID, uuid4

from pydantic import model_validator
from sqlmodel import SQLModel, Field, Relationship

from .answers import TestAnswer, TextAnswer, BaseTestAnswer, BaseTextAnswer, TestAnswerData, TextAnswerData
from ..core.utils import validate_indexes_consistence, validate_text_type_question, validate_single_choice_question, \
    validate_multiple_choice_question

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

    @model_validator(mode="after")
    def validate_types_match(self) -> Self:
        # Question can't contain both test and text answers
        if len(self.test_answers) and len(self.text_answers):
            raise ValueError("Question has both test and text answers")

        if len(self.test_answers):
            # Check that order indexes of the answers are valid
            answer_indexes = set()
            for q in self.test_answers:
                if q.order_index in answer_indexes:
                    raise ValueError("Order indexes of the answers are repeating")
                answer_indexes.add(q.order_index)
            validate_indexes_consistence(answer_indexes)

        if self.type == QuestionTypes.SINGLE_CHOICE:
            validate_single_choice_question(self)
        elif self.type == QuestionTypes.MULTIPLE_CHOICE:
            validate_multiple_choice_question(self)
        elif self.type == QuestionTypes.TEXT:
            validate_text_type_question(self)
        else:
            raise ValueError("Question type couldn't be handled by the validator")

        return self
