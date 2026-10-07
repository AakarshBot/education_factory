from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import median
from typing import Sequence

from channel_history import HistoryEntry

MIN_COMPARISON_SAMPLES = 3
STOP_WORDS = frozenset(
    {
        "and",
        "for",
        "from",
        "in",
        "of",
        "on",
        "the",
        "to",
        "with",
        "question",
        "questions",
        "practice",
        "test",
        "tests",
        "problem",
        "problems",
        "exam",
        "exams",
        "shortcut",
        "shortcuts",
        "method",
        "methods",
    }
)


@dataclass(frozen=True)
class TopicFamilyPerformance:
    subject: str
    family_name: str
    topics: tuple[str, ...]
    topic_count: int
    measured_videos: int
    total_views: float
    average_views: float
    median_views: float
    total_watch_minutes: float
    average_watch_minutes: float
    median_watch_minutes: float
    average_view_percentage: float | None
    engagement_rate_percent: float | None
    subscribers_per_1000_views: float | None
    comparison_ready: bool


def _subject_name(subject: str) -> str:
    normalized = subject.strip().lower()
    return {
        "math": "maths",
        "mathematics": "maths",
        "quant": "maths",
        "quantitative aptitude": "maths",
        "reason": "reasoning",
    }.get(normalized, normalized)


def _topic_tokens(topic: str) -> frozenset[str]:
    words = re.findall(r"[\w]+", topic.casefold(), flags=re.UNICODE)
    tokens = []
    for word in words:
        if word in STOP_WORDS or len(word) <= 2:
            continue
        if word.endswith("s") and not word.endswith(("ss", "is", "us")):
            word = word[:-1]
        tokens.append(word)
    return frozenset(tokens)


def _related(left: frozenset[str], right: frozenset[str]) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    if len(left) == 1 or len(right) == 1:
        return bool(left & right)
    return len(left & right) / len(left | right) >= 0.5


def _metric(entry: HistoryEntry, name: str) -> float | None:
    value = entry.metrics.get(name)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"history metrics contain a non-numeric value for {name}"
        ) from exc


def _family_metrics(
    subject: str,
    family_name: str,
    topics: Sequence[str],
    entries: Sequence[HistoryEntry],
) -> TopicFamilyPerformance:
    valid = []
    for entry in entries:
        if entry.status.strip().lower() != "published" or not entry.video_id:
            continue
        views = _metric(entry, "views")
        if views is None or views < 0:
            raise RuntimeError("history metrics must contain non-negative views")
        valid.append(entry)

    if not valid:
        return TopicFamilyPerformance(
            subject=subject,
            family_name=family_name,
            topics=tuple(sorted(set(topics))),
            topic_count=len(set(topics)),
            measured_videos=0,
            total_views=0.0,
            average_views=0.0,
            median_views=0.0,
            total_watch_minutes=0.0,
            average_watch_minutes=0.0,
            median_watch_minutes=0.0,
            average_view_percentage=None,
            engagement_rate_percent=None,
            subscribers_per_1000_views=None,
            comparison_ready=False,
        )

    views = [_metric(entry, "views") or 0.0 for entry in valid]
    watch_minutes = [
        _metric(entry, "estimatedMinutesWatched") or 0.0 for entry in valid
    ]
    view_percentages = [
        value
        for value in (_metric(entry, "averageViewPercentage") for entry in valid)
        if value is not None
    ]
    total_views = sum(views)
    total_watch_minutes = sum(watch_minutes)
    total_likes = sum(_metric(entry, "likes") or 0.0 for entry in valid)
    total_comments = sum(_metric(entry, "comments") or 0.0 for entry in valid)
    total_subscribers = sum(
        _metric(entry, "subscribersGained") or 0.0 for entry in valid
    )

    return TopicFamilyPerformance(
        subject=subject,
        family_name=family_name,
        topics=tuple(sorted(set(topics))),
        topic_count=len(set(topics)),
        measured_videos=len(valid),
        total_views=total_views,
        average_views=total_views / len(valid),
        median_views=float(median(views)),
        total_watch_minutes=total_watch_minutes,
        average_watch_minutes=total_watch_minutes / len(valid),
        median_watch_minutes=float(median(watch_minutes)),
        average_view_percentage=(
            sum(view_percentages) / len(view_percentages)
            if view_percentages
            else None
        ),
        engagement_rate_percent=(
            ((total_likes + total_comments) / total_views) * 100
            if total_views > 0
            else None
        ),
        subscribers_per_1000_views=(
            (total_subscribers / total_views) * 1000
            if total_views > 0
            else None
        ),
        comparison_ready=len(valid) >= MIN_COMPARISON_SAMPLES,
    )


def analyze_topic_families(
    entries: Sequence[HistoryEntry],
) -> tuple[TopicFamilyPerformance, ...]:
    subject_entries: dict[str, list[HistoryEntry]] = {}
    for entry in entries:
        subject = _subject_name(entry.subject)
        if subject:
            subject_entries.setdefault(subject, []).append(entry)

    families: list[TopicFamilyPerformance] = []

    for subject, subject_items in sorted(subject_entries.items()):
        topic_tokens: dict[str, frozenset[str]] = {}
        topic_entries: dict[str, list[HistoryEntry]] = {}

        for entry in subject_items:
            topic = entry.topic.strip()
            if not topic:
                continue
            key = topic.casefold()
            topic_tokens.setdefault(key, _topic_tokens(topic))
            topic_entries.setdefault(key, []).append(entry)

        unassigned = set(topic_tokens)
        while unassigned:
            seed = sorted(unassigned)[0]
            component = {seed}
            changed = True

            while changed:
                changed = False
                for candidate in sorted(unassigned - component):
                    if any(
                        _related(topic_tokens[candidate], topic_tokens[item])
                        for item in component
                    ):
                        component.add(candidate)
                        changed = True

            unassigned -= component
            topics = [min(topic_entries[key], key=lambda item: len(item.topic)).topic for key in component]
            grouped_entries = [
                item
                for key in component
                for item in topic_entries[key]
            ]
            family_name = min(topics, key=lambda topic: (len(topic), topic.casefold()))
            families.append(
                _family_metrics(
                    subject,
                    family_name,
                    topics,
                    grouped_entries,
                )
            )

    return tuple(
        sorted(
            families,
            key=lambda item: (
                not item.comparison_ready,
                -item.median_views,
                -item.measured_videos,
                item.subject,
                item.family_name.casefold(),
            ),
        )
    )
