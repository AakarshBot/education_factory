from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

from editorial_queue import EditorialJob

DEFAULT_BACKLOG_FILE = Path("data/production_backlog.json")
STALE_CLAIM_HOURS = 168


@dataclass(frozen=True)
class BacklogEntry:
    priority: int
    exam: str
    subject: str
    topic: str
    total_score: float
    supporting_signal_indices: tuple[int, ...]
    rationale: str
    created_at: str
    status: str = "pending"
    claimed_run_id: str | None = None
    claimed_at: str | None = None

    @property
    def key(self) -> tuple[str, str, str]:
        return (
            self.exam.strip().lower(),
            self.subject.strip().lower(),
            self.topic.strip().lower(),
        )

    def to_job(self) -> EditorialJob:
        return EditorialJob(
            priority=self.priority,
            exam=self.exam,
            subject=self.subject,
            topic=self.topic,
            total_score=self.total_score,
            supporting_signal_indices=self.supporting_signal_indices,
            rationale=self.rationale,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority": self.priority,
            "exam": self.exam,
            "subject": self.subject,
            "topic": self.topic,
            "total_score": self.total_score,
            "supporting_signal_indices": list(self.supporting_signal_indices),
            "rationale": self.rationale,
            "created_at": self.created_at,
            "status": self.status,
            "claimed_run_id": self.claimed_run_id,
            "claimed_at": self.claimed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BacklogEntry":
        if not isinstance(data, dict):
            raise ValueError("backlog entry must be an object")
        status = str(data.get("status", "pending")).strip().lower()
        if status not in {"pending", "claimed"}:
            raise ValueError("backlog entry status must be pending or claimed")
        indices = data.get("supporting_signal_indices", [])
        if not isinstance(indices, list):
            raise ValueError("backlog supporting indices must be a list")
        return cls(
            priority=int(data["priority"]),
            exam=str(data["exam"]),
            subject=str(data["subject"]),
            topic=str(data["topic"]),
            total_score=float(data["total_score"]),
            supporting_signal_indices=tuple(int(index) for index in indices),
            rationale=str(data["rationale"]),
            created_at=str(data["created_at"]),
            status=status,
            claimed_run_id=data.get("claimed_run_id"),
            claimed_at=data.get("claimed_at"),
        )


def load_backlog(path: Path = DEFAULT_BACKLOG_FILE) -> list[BacklogEntry]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read production backlog: {path}") from exc
    if not isinstance(data, list):
        raise RuntimeError("Production backlog must contain a JSON array")
    try:
        return [BacklogEntry.from_dict(item) for item in data]
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Production backlog contains an invalid entry") from exc


def save_backlog(
    entries: Sequence[BacklogEntry],
    path: Path = DEFAULT_BACKLOG_FILE,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [entry.to_dict() for entry in entries]
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            temp_path = Path(handle.name)
        temp_path.replace(path)
    except OSError as exc:
        raise RuntimeError(f"Could not write production backlog: {path}") from exc


def merge_jobs(
    entries: Sequence[BacklogEntry],
    jobs: Sequence[EditorialJob],
    *,
    now: datetime | None = None,
) -> list[BacklogEntry]:
    created_at = (now or datetime.now(timezone.utc)).isoformat()
    merged = list(entries)
    positions = {entry.key: index for index, entry in enumerate(merged)}

    for job in jobs:
        key = (
            job.exam.strip().lower(),
            job.subject.strip().lower(),
            job.topic.strip().lower(),
        )
        entry = BacklogEntry(
            priority=job.priority,
            exam=job.exam,
            subject=job.subject,
            topic=job.topic,
            total_score=job.total_score,
            supporting_signal_indices=job.supporting_signal_indices,
            rationale=job.rationale,
            created_at=created_at,
        )
        existing_index = positions.get(key)
        if existing_index is None:
            positions[key] = len(merged)
            merged.append(entry)
        elif merged[existing_index].status == "pending":
            merged[existing_index] = entry

    return sorted(
        merged,
        key=lambda item: (
            0 if item.status == "pending" else 1,
            -item.total_score,
            item.priority,
            item.key,
        ),
    )


def release_stale_claims(
    entries: Sequence[BacklogEntry],
    *,
    now: datetime | None = None,
    max_age_hours: int = STALE_CLAIM_HOURS,
) -> list[BacklogEntry]:
    if max_age_hours < 1:
        raise ValueError("max_age_hours must be at least 1")
    reference = now or datetime.now(timezone.utc)
    cutoff = reference - timedelta(hours=max_age_hours)
    released: list[BacklogEntry] = []

    for entry in entries:
        if entry.status != "claimed" or not entry.claimed_at:
            released.append(entry)
            continue
        try:
            claimed = datetime.fromisoformat(entry.claimed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise RuntimeError("Production backlog contains an invalid claimed_at") from exc
        if claimed < cutoff:
            released.append(
                BacklogEntry(
                    priority=entry.priority,
                    exam=entry.exam,
                    subject=entry.subject,
                    topic=entry.topic,
                    total_score=entry.total_score,
                    supporting_signal_indices=entry.supporting_signal_indices,
                    rationale=entry.rationale,
                    created_at=entry.created_at,
                )
            )
        else:
            released.append(entry)

    return released


def claim_job(
    entries: Sequence[BacklogEntry],
    job: EditorialJob,
    *,
    run_id: str,
    now: datetime | None = None,
) -> list[BacklogEntry]:
    claimed_at = (now or datetime.now(timezone.utc)).isoformat()
    key = (
        job.exam.strip().lower(),
        job.subject.strip().lower(),
        job.topic.strip().lower(),
    )
    updated: list[BacklogEntry] = []
    found = False

    for entry in entries:
        if entry.key != key:
            updated.append(entry)
            continue
        if entry.status != "pending":
            raise RuntimeError(f"backlog job is not pending: {key}")
        updated.append(
            BacklogEntry(
                priority=entry.priority,
                exam=entry.exam,
                subject=entry.subject,
                topic=entry.topic,
                total_score=entry.total_score,
                supporting_signal_indices=entry.supporting_signal_indices,
                rationale=entry.rationale,
                created_at=entry.created_at,
                status="claimed",
                claimed_run_id=run_id,
                claimed_at=claimed_at,
            )
        )
        found = True

    if not found:
        raise RuntimeError(f"backlog job was not found: {key}")
    return updated


def complete_job(
    entries: Sequence[BacklogEntry],
    *,
    exam: str,
    subject: str,
    topic: str,
    run_id: str,
) -> list[BacklogEntry]:
    key = (
        exam.strip().lower(),
        subject.strip().lower(),
        topic.strip().lower(),
    )
    remaining: list[BacklogEntry] = []
    for entry in entries:
        if entry.key != key:
            remaining.append(entry)
            continue
        if entry.status != "claimed" or entry.claimed_run_id != run_id:
            raise RuntimeError(f"backlog job is not claimed by run: {key}")
    return remaining


def pending_jobs(entries: Sequence[BacklogEntry]) -> list[EditorialJob]:
    return [entry.to_job() for entry in entries if entry.status == "pending"]
