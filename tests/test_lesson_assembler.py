import pytest

from lesson_assembler import assemble_lesson
from question import Question


def make_question(index=1, *, source_type="original", source_reference=None, shortcut="Use the shortcut."):
    return Question(
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        difficulty="medium",
        question=f"Question {index}",
        choices=("A", "B", "C", "D"),
        correct_answer="A",
        explanation="The verified answer follows from the calculation.",
        shortcut=shortcut,
        source_type=source_type,
        source_reference=source_reference,
    )


def kinds(lesson):
    return [segment.kind for segment in lesson.segments]


def test_practice_sequences_question_answer_explanation_and_shortcut():
    lesson = assemble_lesson(
        [make_question(1), make_question(2, shortcut=None)],
        lesson_type="practice",
    )

    assert kinds(lesson) == [
        "question", "answer", "explanation", "shortcut",
        "question", "answer", "explanation",
    ]
    assert lesson.lesson_type == "practice"
    assert lesson.questions[0].correct_answer == "A"


def test_timed_test_adds_timer_before_answer():
    lesson = assemble_lesson([make_question()], lesson_type="timed_test")

    assert kinds(lesson) == ["question", "timer", "answer", "explanation", "shortcut"]
    timer = lesson.segments[1]
    assert timer.duration_seconds == 15


def test_concept_practice_starts_with_supplied_concept():
    lesson = assemble_lesson(
        [make_question()],
        lesson_type="concept_practice",
        concept_summary="Percentage means a value out of 100.",
    )

    assert kinds(lesson) == ["concept", "question", "answer", "explanation", "shortcut"]
    assert lesson.segments[0].text == "Percentage means a value out of 100."


def test_concept_practice_requires_real_concept_text():
    with pytest.raises(ValueError, match="concept_summary is required"):
        assemble_lesson([make_question()], lesson_type="concept_practice")


def test_pyq_analysis_requires_pyq_source_and_reference():
    lesson = assemble_lesson(
        [make_question(source_type="pyq", source_reference="SSC CGL 2024 Tier 1")],
        lesson_type="pyq_analysis",
    )

    assert kinds(lesson) == ["source", "question", "answer", "explanation", "shortcut"]
    assert lesson.segments[0].source_reference == "SSC CGL 2024 Tier 1"

    with pytest.raises(ValueError, match="not a PYQ"):
        assemble_lesson([make_question()], lesson_type="pyq_analysis")

    with pytest.raises(ValueError, match="missing source_reference"):
        assemble_lesson(
            [make_question(source_type="pyq")],
            lesson_type="pyq_analysis",
        )


def test_revision_is_a_normal_question_loop_with_shortcuts():
    lesson = assemble_lesson([make_question(1), make_question(2)], lesson_type="revision")

    assert kinds(lesson) == [
        "question", "answer", "explanation", "shortcut",
        "question", "answer", "explanation", "shortcut",
    ]
    assert lesson.title.endswith("Revision Marathon")


def test_custom_title_is_used():
    lesson = assemble_lesson(
        [make_question()],
        lesson_type="practice",
        title="Percentages: 10 Questions",
    )
    assert lesson.title == "Percentages: 10 Questions"


def test_assembler_rejects_missing_explanation():
    question = make_question()
    question = Question(**{**question.to_dict(), "explanation": ""})
    with pytest.raises(ValueError, match="has no explanation"):
        assemble_lesson([question], lesson_type="practice")


def test_assembler_rejects_invalid_input():
    with pytest.raises(ValueError, match="must not be empty"):
        assemble_lesson([], lesson_type="practice")
    with pytest.raises(ValueError, match="unsupported lesson_type"):
        assemble_lesson([make_question()], lesson_type="unknown")
