from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from question import Question


@dataclass(frozen=True)
class VerifiedPYQSource:
    question: Question
    source_reference: str
    rights_note: str

    def __post_init__(self) -> None:
        if not isinstance(self.question, Question):
            raise TypeError("question must be a Question")
        if self.question.source_type.strip().lower() != "pyq":
            raise ValueError("question source_type must be pyq")
        if not self.question.source_reference or not self.question.source_reference.strip():
            raise ValueError("question must contain source_reference")
        if self.question.source_reference.strip() != self.source_reference.strip():
            raise ValueError("source_reference must match the question")
        if not isinstance(self.rights_note, str) or not self.rights_note.strip():
            raise ValueError("rights_note must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question.to_dict(),
            "source_reference": self.source_reference,
            "rights_note": self.rights_note,
        }


def select_verified_pyq_questions(
    sources: Sequence[VerifiedPYQSource],
    *,
    count: int,
) -> list[Question]:
    if count < 1:
        raise ValueError("count must be at least 1")
    if not sources:
        raise ValueError("verified PYQ sources are required")
    if len(sources) < count:
        raise ValueError("not enough verified PYQ sources")

    questions = []
    seen: set[tuple[str, str, str]] = set()
    for source in sources[:count]:
        question = source.question
        key = (
            question.exam.strip().lower(),
            question.topic.strip().lower(),
            question.question.strip().lower(),
        )
        if key in seen:
            raise RuntimeError("verified PYQ sources contain duplicate questions")
        seen.add(key)
        questions.append(question)
    return questions
