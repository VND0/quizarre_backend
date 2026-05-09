from typing import TYPE_CHECKING

from ..core.constants import QuestionTypes

if TYPE_CHECKING:
    from ..models.quizzes import QuizUpload, Quiz
    from ..models.questions import QuestionUpload, Question
    from ..models.answers import TestAnswer


def validate_indexes_consistence(indexes: set[int]):
    indexes = sorted(indexes)
    counter = 0
    for i in indexes:
        if i != counter:
            raise ValueError("Order indexes are inconsistent")
        counter += 1


def validate_questions_indexes(quiz: Quiz | QuizUpload):
    indexes = set()
    for q in quiz.questions:
        if q.order_index in indexes:
            raise ValueError("Order indexes of the questions are repeating")
        indexes.add(q.order_index)

    validate_indexes_consistence(indexes)


def validate_answers(question: QuestionUpload | Question):
    # Question can't contain both test and text answers
    if len(question.test_answers) and len(question.text_answers):
        raise ValueError("Question has both test and text answers")

    if len(question.test_answers):
        # Check that order indexes of the answers are valid
        indexes = set()
        for q in question.test_answers:
            if q.order_index in indexes:
                raise ValueError("Order indexes of the answers are repeating")
            indexes.add(q.order_index)

        validate_indexes_consistence(indexes)

    if question.type == QuestionTypes.SINGLE_CHOICE:
        validate_single_choice_question(question)
    elif question.type == QuestionTypes.MULTIPLE_CHOICE:
        validate_multiple_choice_question(question)
    elif question.type == QuestionTypes.TEXT:
        validate_text_type_question(question)
    else:
        raise ValueError("Question type couldn't be handled by the validator")


def validate_single_choice_question(question: QuestionUpload):
    # There must be exactly one correct option
    counter = 0
    for a in question.test_answers:
        counter += a.is_correct
        if counter == 2:
            raise ValueError("Single choice question has more than one correct answer")
    if counter == 0:
        raise ValueError("Single choice question has no correct answers")


def validate_multiple_choice_question(question: QuestionUpload):
    # There must be at least one correct option
    for a in question.test_answers:
        if a.is_correct:
            return
    raise ValueError("Multiple choice question has no correct answers")


def validate_text_type_question(question: QuestionUpload):
    # There must be at least one correct answer
    if not len(question.text_answers):
        raise ValueError("Text question has no answers")


def move_order_indexes(objects: list[Question | TestAnswer], ge: int, decrement=False):
    for obj in objects:
        if obj.order_index >= ge:
            obj.order_index += 1 if not decrement else -1
