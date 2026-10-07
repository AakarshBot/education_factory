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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Lesson":
        return cls(
            lesson_type=data["lesson_type"],
            title=data["title"],
            subject=data["subject"],
            exam=data["exam"],
            topic=data["topic"],
            questions=tuple(Question.from_dict(item) for item in data["questions"]),
            segments=tuple(
                LessonSegment(
                    kind=item["kind"],
                    question_index=item.get("question_index"),
                    text=item.get("text"),
                    duration_seconds=item.get("duration_seconds"),
                    source_reference=item.get("source_reference"),
                )
                for item in data["segments"]
            ),
        )
