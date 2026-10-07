import pytest

from pyq_source import VerifiedPYQSource, select_verified_pyq_questions
from question import Question


def question(reference, question_text):
    return Question(
        subject="maths",
        exam="SSC",
        topic="percentages",
        difficulty="medium",
        question=question_text,
        choices=("25", "50", "75", "100"),
        correct_answer="25",
        explanation="",
        shortcut=None,
        source_type="pyq",
        source_reference=reference,
    )


def source(reference, text):
    q = question(reference, text)
    return VerifiedPYQSource(
        question=q,
        source_reference=reference,
        rights_note="Verified official source and permitted educational reuse.",
    )


def test_verified_pyq_source_requires_matching_reference():
    q = question("https://official.example/q1", "A")
    with pytest.raises(ValueError, match="match"):
        VerifiedPYQSource(
            question=q,
            source_reference="https://official.example/q2",
            rights_note="verified",
        )


def test_select_verified_pyq_questions_requires_enough_sources():
    with pytest.raises(ValueError, match="not enough"):
        select_verified_pyq_questions([source("a", "A")], count=2)


def test_select_verified_pyq_questions_returns_verified_questions():
    result = select_verified_pyq_questions(
        [source("a", "A"), source("b", "B")],
        count=2,
    )
    assert [item.source_reference for item in result] == ["a", "b"]
