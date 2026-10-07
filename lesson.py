from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from question import Question


@dataclass(frozen=True)
class LessonSegment:
    kind: str
    question_index: int | None = None
    text: str | None = None
    duration_seconds: int | None = None
    source_reference: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "question_index": self.question_index,
            "text": self.text,
            "duration_seconds": self.duration_seconds,
            "source_reference": self.source_reference,
        }


@dataclass(frozen=True)
class Lesson:
    lesson_type: str
    title: str
    subject: str
    exam: str
    topic: str
    questions: tuple[Question, ...]
    segments: tuple[LessonSegment, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_type": self.lesson_type,
            "title": self.title,
            "subject": self.subject,
            "exam": self.exam,
            "topic": self.topic,
            "questions": [question.to_dict() for question in self.questions],
            "segments": [segment.to_dict() for segment in self.segments],
        }
