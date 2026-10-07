from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

DEFAULT_HISTORY_FILE = Path("data/channel_history.json")
ACTIVE_STATUSES = frozenset({"published", "scheduled"})


@dataclass(frozen=True)
class HistoryEntry:
    exam: str
    subject: str
    topic: str
    lesson_type: str
    title: str
    status: str
    created_at: str
    video_id: str | None = None
    published_at: str | None = None
    metrics: Mapping[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "exam": self.exam,
            "subject": self.subject,
            "topic": self.topic,
            "lesson_type": self.lesson_type,
            "title": self.title,
            "status": self.status,
            "created_at": self.created_at,
            "video_id": self.video_id,
            "published_at": self.published_at,
            "metrics": dict(self.metrics),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HistoryEntry":
        metrics = data.get("metrics", {})
        if not isinstance(metrics, dict):
            raise ValueError("history metrics must be an object")
        return cls(
            exam=str(data["exam"]),
            subject=str(data["subject"]),
            topic=str(data["topic"]),
            lesson_type=str(data["lesson_type"]),
            title=str(data["title"]),
            status=str(data["status"]),
            created_at=str(data["created_at"]),
            video_id=data.get("video_id"),
            published_at=data.get("published_at"),
            metrics={str(key): float(value) for key, value in metrics.items()},
        )


def topic_key(exam: str, subject: str, topic: str) -> tuple[str, str, str]:
    return (exam.strip().lower(), subject.strip().lower(), topic.strip().lower())


def load_history(path: Path = DEFAULT_HISTORY_FILE) -> list[HistoryEntry]:
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read channel history: {path}") from exc

    if not isinstance(data, list):
        raise RuntimeError("Channel history must contain a JSON array")

    try:
        return [HistoryEntry.from_dict(item) for item in data]
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Channel history contains an invalid entry") from exc


def save_history(
    entries: Sequence[HistoryEntry],
    path: Path = DEFAULT_HISTORY_FILE,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [entry.to_dict() for entry in entries]
    try:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(f"Could not write channel history: {path}") from exc


def append_history(
    entry: HistoryEntry,
    path: Path = DEFAULT_HISTORY_FILE,
) -> None:
    save_history([*load_history(path), entry], path)


def recent_topic_keys(
    entries: Sequence[HistoryEntry],
    *,
    days: int = 30,
    now: datetime | None = None,
) -> set[tuple[str, str, str]]:
    if days < 1:
        raise ValueError("days must be at least 1")

    reference = now or datetime.now(timezone.utc)
    cutoff = reference - timedelta(days=days)
    keys: set[tuple[str, str, str]] = set()

    for entry in entries:
        if entry.status.strip().lower() not in ACTIVE_STATUSES:
            continue

        try:
            created = datetime.fromisoformat(entry.created_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise RuntimeError("Channel history contains an invalid created_at") from exc

        if created >= cutoff:
            keys.add(topic_key(entry.exam, entry.subject, entry.topic))

    return keys
