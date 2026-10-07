from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Sequence

from channel_history import HistoryEntry

MIN_COMPARISON_SAMPLES = 3
CORE_SUBJECTS = ("maths", "reasoning", "english")


@dataclass(frozen=True)
class SubjectPerformance:
    subject: str
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


def _metric(entry: HistoryEntry, name: str) -> float | None:
    value = entry.metrics.get(name)
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"history metrics contain a non-numeric value for {name}"
        ) from exc
    return numeric


def _analyze_entries(
    subject: str,
    entries: Sequence[HistoryEntry],
) -> SubjectPerformance:
    valid = []
    for entry in entries:
        if entry.content_format != "long_form" or entry.status.strip().lower() != "published" or not entry.video_id:
            continue
        views = _metric(entry, "views")
        if views is None or views < 0:
            raise RuntimeError("history metrics must contain non-negative views")
        valid.append(entry)

    if not valid:
        return SubjectPerformance(
            subject=subject,
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

    return SubjectPerformance(
        subject=subject,
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


def analyze_subjects(
    entries: Sequence[HistoryEntry],
) -> tuple[SubjectPerformance, ...]:
    groups = {subject: [] for subject in CORE_SUBJECTS}

    for entry in entries:
        subject = _subject_name(entry.subject)
        if subject in groups:
            groups[subject].append(entry)

    return tuple(
        _analyze_entries(subject, groups[subject])
        for subject in CORE_SUBJECTS
    )
