from __future__ import annotations

from collections.abc import Sequence

from lesson import Lesson, LessonSegment
from question import Question

LESSON_TYPES = (
    "practice",
    "timed_test",
    "concept_practice",
    "pyq_analysis",
    "revision",
)


def _validate_questions(questions: Sequence[Question]) -> tuple[Question, ...]:
    if not questions:
        raise ValueError("questions must not be empty")

    items = tuple(questions)
    for index, question in enumerate(items):
        if not isinstance(question, Question):
            raise TypeError(f"question {index} is not a Question")
        if not question.explanation.strip():
            raise ValueError(f"question {index} has no explanation")
    return items


def _build_title(lesson_type: str, question: Question) -> str:
    labels = {
        "practice": "Practice",
        "timed_test": "Timed Test",
        "concept_practice": "Concept + Practice",
        "pyq_analysis": "PYQ Analysis",
        "revision": "Revision Marathon",
    }
    return f"{question.exam} {question.subject} — {question.topic}: {labels[lesson_type]}"


def _question_sequence(
    questions: tuple[Question, ...],
    *,
    timed: bool,
    include_source: bool,
) -> list[LessonSegment]:
    segments: list[LessonSegment] = []
    for index, question in enumerate(questions):
        if include_source:
            segments.append(
                LessonSegment(
                    kind="source",
                    question_index=index,
                    source_reference=question.source_reference,
                )
            )
        segments.append(LessonSegment(kind="question", question_index=index))
        if timed:
            segments.append(
                LessonSegment(kind="timer", question_index=index, duration_seconds=15)
            )
        segments.append(LessonSegment(kind="answer", question_index=index))
        segments.append(LessonSegment(kind="explanation", question_index=index))
        if question.shortcut:
            segments.append(LessonSegment(kind="shortcut", question_index=index))
    return segments


def assemble_lesson(
    questions: Sequence[Question],
    *,
    lesson_type: str,
    title: str | None = None,
    concept_summary: str | None = None,
) -> Lesson:
    items = _validate_questions(questions)
    if lesson_type not in LESSON_TYPES:
        raise ValueError(f"unsupported lesson_type: {lesson_type}")

    first = items[0]

    if lesson_type == "concept_practice":
        if not concept_summary or not concept_summary.strip():
            raise ValueError("concept_summary is required for concept_practice")
        segments = [LessonSegment(kind="concept", text=concept_summary.strip())]
        segments.extend(_question_sequence(items, timed=False, include_source=False))
    elif lesson_type == "timed_test":
        segments = _question_sequence(items, timed=True, include_source=False)
    elif lesson_type == "pyq_analysis":
        for index, question in enumerate(items):
            if question.source_type.lower() != "pyq":
                raise ValueError(f"question {index} is not a PYQ")
            if not question.source_reference or not question.source_reference.strip():
                raise ValueError(f"question {index} is missing source_reference")
        segments = _question_sequence(items, timed=False, include_source=True)
    else:
        segments = _question_sequence(items, timed=False, include_source=False)

    return Lesson(
        lesson_type=lesson_type,
        title=title.strip() if title and title.strip() else _build_title(lesson_type, first),
        subject=first.subject,
        exam=first.exam,
        topic=first.topic,
        questions=items,
        segments=tuple(segments),
    )
