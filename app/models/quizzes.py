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


class QuestionResponse(BaseQuestion):
    test_answers: list[BaseTestAnswer] = Field(alias="testAnswers")
    text_answers: list[BaseTextAnswer] = Field(alias="textAnswers")


class FullQuizResponse(BaseQuiz):
    questions: list[QuestionResponse]


class QuestionUpload(QuestionData):
    test_answers: list[TestAnswerData] = Field(alias="testAnswers")
    text_answers: list[TextAnswerData] = Field(alias="textAnswers")


class QuizUpload(QuizData):
    questions: list[QuestionUpload]
