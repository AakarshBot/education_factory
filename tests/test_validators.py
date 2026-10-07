import pytest
from fractions import Fraction

from question import Question
from validators import (
    ValidationError,
    evaluate_math_expression,
    parse_numeric_answer,
    validate_math_answer,
    validate_question,
)


def make_math_question(answer="₹1,700", choices=None):
    return Question(
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        difficulty="medium",
        question="A ₹2,000 item is reduced by 15%. What is the selling price?",
        choices=choices,
        correct_answer=answer,
        explanation="15% of ₹2,000 is ₹300, so the answer is ₹1,700.",
        shortcut="Multiply by 0.85.",
        source_type="original",
        source_reference=None,
    )


def test_math_expression_is_exact():
    assert evaluate_math_expression("2000 * (1 - 15 / 100)") == Fraction(1700)


def test_numeric_answer_parser_handles_common_number_forms():
    assert parse_numeric_answer("₹1,700") == Fraction(1700)
    assert parse_numeric_answer("1,700") == Fraction(1700)
    assert parse_numeric_answer("3/4") == Fraction(3, 4)


def test_valid_math_answer_passes():
    validate_math_answer("2000 * (1 - 15 / 100)", "₹1,700")


def test_wrong_math_answer_fails():
    with pytest.raises(ValidationError, match="answer mismatch"):
        validate_math_answer("2000 * (1 - 15 / 100)", "₹1,650")


def test_unsafe_math_expression_fails():
    with pytest.raises(ValidationError):
        evaluate_math_expression("__import__('os').system('echo bad')")


def test_math_question_requires_machine_checkable_expression():
    question = make_math_question()
    with pytest.raises(ValidationError, match="machine-checkable expression"):
        validate_question(question)


def test_math_question_uses_expression_and_passes():
    validate_question(
        make_math_question(),
        math_expression="2000 * (1 - 15 / 100)",
    )


def test_multiple_choice_answer_must_be_present_and_unique():
    question = make_math_question(
        choices=("₹1,600", "₹1,700", "₹1,800", "₹1,900")
    )
    validate_question(question, math_expression="2000 * (1 - 15 / 100)")

    duplicate = make_math_question(
        choices=("₹1,700", "₹1,700", "₹1,800", "₹1,900")
    )
    with pytest.raises(ValidationError, match="unique"):
        validate_question(
            duplicate,
            math_expression="2000 * (1 - 15 / 100)",
        )
