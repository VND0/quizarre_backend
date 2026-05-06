from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.questions import QuestionUpload


def validate_indexes_consistence(indexes: set[int]):
    indexes = sorted(indexes)
    counter = 0
    for i in indexes:
        if i != counter:
            raise ValueError("Order indexes are inconsistent")
        counter += 1


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