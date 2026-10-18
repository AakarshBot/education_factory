from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from channel_history import ACTIVE_STATUSES, HistoryEntry, recent_topic_keys
from topic_family_analysis import topics_are_related
from topic_scorer import TopicScore

RELATED_TOPIC_COOLDOWN_DAYS = 14


@dataclass(frozen=True)
class EditorialJob:
    priority: int
    exam: str
    subject: str
    topic: str
    total_score: float
    supporting_signal_indices: tuple[int, ...]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority": self.priority,
            "exam": self.exam,
            "subject": self.subject,
            "topic": self.topic,
            "total_score": self.total_score,
            "supporting_signal_indices": self.supporting_signal_indices,
            "rationale": self.rationale,
        }


def has_recent_related_topic(
    subject: str,
    topic: str,
    history: Sequence[HistoryEntry],
    *,
    days: int = RELATED_TOPIC_COOLDOWN_DAYS,
    now: datetime | None = None,
) -> bool:
    """Check whether this subject has had a materially similar recent lesson."""
    if days < 1:
        raise ValueError("days must be at least 1")
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None or reference.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    cutoff = reference - timedelta(days=days)
    subject_key = subject.strip().casefold()

    for entry in history:
        if entry.status.strip().lower() not in ACTIVE_STATUSES:
            continue
        if entry.subject.strip().casefold() != subject_key or not entry.topic.strip():
            continue
        try:
            created = datetime.fromisoformat(entry.created_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise RuntimeError("Channel history contains an invalid created_at") from exc
        if created.tzinfo is None or created.utcoffset() is None:
            created = created.replace(tzinfo=timezone.utc)
        else:
            created = created.astimezone(timezone.utc)
        if created >= cutoff and topics_are_related(topic, entry.topic):
            return True
    return False


def build_editorial_queue(
    scores: Sequence[TopicScore],
    *,
    max_jobs: int = 5,
    history: Sequence[HistoryEntry] = (),
    history_days: int = 30,
    now: datetime | None = None,
) -> list[EditorialJob]:
    if not scores:
        raise ValueError("scores must not be empty")
    if max_jobs < 1:
        raise ValueError("max_jobs must be at least 1")
    excluded_topics = recent_topic_keys(history, days=history_days, now=now)

    ranked = sorted(
        scores,
        key=lambda item: (
            -item.total_score,
            item.exam.lower(),
            item.subject.lower(),
            item.topic.lower(),
        ),
    )

    jobs: list[EditorialJob] = []
    related_fallbacks: list[TopicScore] = []
    seen: set[tuple[str, str, str]] = set()

    for score in ranked:
        key = (
            score.exam.strip().lower(),
            score.subject.strip().lower(),
            score.topic.strip().lower(),
        )
        if key in seen or key in excluded_topics:
            continue
        seen.add(key)
        if has_recent_related_topic(
            score.subject,
            score.topic,
            history,
            days=RELATED_TOPIC_COOLDOWN_DAYS,
            now=now,
        ):
            related_fallbacks.append(score)
            continue

        jobs.append(
            EditorialJob(
                priority=len(jobs) + 1,
                exam=score.exam,
                subject=score.subject,
                topic=score.topic,
                total_score=score.total_score,
                supporting_signal_indices=score.supporting_signal_indices,
                rationale=score.rationale,
            )
        )
        if len(jobs) == max_jobs:
            break

    if not jobs and related_fallbacks:
        score = related_fallbacks[0]
        jobs.append(
            EditorialJob(
                priority=1,
                exam=score.exam,
                subject=score.subject,
                topic=score.topic,
                total_score=score.total_score,
                supporting_signal_indices=score.supporting_signal_indices,
                rationale=(
                    f"{score.rationale} Fallback: no distinct eligible topic "
                    "was available after recent-related-topic filtering."
                ),
            )
        )

    return jobs
