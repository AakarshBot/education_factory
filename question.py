from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Question:
    subject: str
    exam: str
    topic: str
    difficulty: str
    question: str
    choices: tuple[str, ...] | None
    correct_answer: str
    explanation: str
    shortcut: str | None
    source_type: str
    source_reference: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Question":
        choices = data.get("choices")
        if choices is not None:
            choices = tuple(choices)

        return cls(
            subject=data["subject"],
            exam=data["exam"],
            topic=data["topic"],
            difficulty=data["difficulty"],
            question=data["question"],
            choices=choices,
            correct_answer=data["correct_answer"],
            explanation=data["explanation"],
            shortcut=data.get("shortcut"),
            source_type=data["source_type"],
            source_reference=data.get("source_reference"),
        )
