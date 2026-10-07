from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from channel_history import HistoryEntry, recent_topic_keys
from topic_scorer import TopicScore


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


def build_editorial_queue(
    scores: Sequence[TopicScore],
    *,
    max_jobs: int = 5,
    history: Sequence[HistoryEntry] = (),
    history_days: int = 30,
) -> list[EditorialJob]:
    if not scores:
        raise ValueError("scores must not be empty")
    if max_jobs < 1:
        raise ValueError("max_jobs must be at least 1")
    excluded_topics = recent_topic_keys(history, days=history_days)

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

    return jobs
