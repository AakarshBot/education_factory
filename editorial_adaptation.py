from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from format_analysis import FormatPerformance
from subject_analysis import SubjectPerformance
from topic_family_analysis import TopicFamilyPerformance

MIN_READY_GROUPS = 2
MIN_WEIGHT = 0.90
MAX_WEIGHT = 1.10


@dataclass(frozen=True)
class EditorialAdaptation:
    format_weights: Mapping[str, float]
    subject_weights: Mapping[str, float]
    topic_family_weights: Mapping[tuple[str, str], float]
    format_ready: bool
    subject_ready: bool
    topic_family_ready: bool


def _weight_map(
    items: Sequence[tuple[str, float, int, bool]],
) -> tuple[dict[str, float], bool]:
    ready = [(name, value, count) for name, value, count, is_ready in items if is_ready]
    if len(ready) < MIN_READY_GROUPS:
        return ({name: 1.0 for name, _, _, _ in items}, False)

    baseline = sum(value for _, value, _ in ready) / len(ready)
    if baseline <= 0:
        return ({name: 1.0 for name, _, _, _ in items}, False)

    weights: dict[str, float] = {}
    for name, value, _, is_ready in items:
        if not is_ready or value <= 0:
            weights[name] = 1.0
            continue
        relative = value / baseline
        adjustment = max(-0.20, min(0.20, relative - 1.0)) * 0.50
        weights[name] = round(
            max(MIN_WEIGHT, min(MAX_WEIGHT, 1.0 + adjustment)),
            4,
        )

    return weights, True


def build_editorial_adaptation(
    formats: Sequence[FormatPerformance],
    subjects: Sequence[SubjectPerformance],
    topic_families: Sequence[TopicFamilyPerformance],
) -> EditorialAdaptation:
    format_weights, format_ready = _weight_map(
        [
            (
                item.lesson_type,
                item.median_views,
                item.measured_videos,
                item.comparison_ready,
            )
            for item in formats
        ]
    )
    subject_weights, subject_ready = _weight_map(
        [
            (
                item.subject,
                item.median_views,
                item.measured_videos,
                item.comparison_ready,
            )
            for item in subjects
        ]
    )

    family_items = [
        (
            (item.subject, item.family_name),
            item.median_views,
            item.measured_videos,
            item.comparison_ready,
        )
        for item in topic_families
    ]
    family_values, family_ready = _weight_map(
        [
            (f"{subject}\t{family}", value, count, ready)
            for (subject, family), value, count, ready in family_items
        ]
    )
    topic_family_weights = {
        (subject, family): family_values[f"{subject}\t{family}"]
        for (subject, family), _, _, _ in family_items
    }

    return EditorialAdaptation(
        format_weights=format_weights,
        subject_weights=subject_weights,
        topic_family_weights=topic_family_weights,
        format_ready=format_ready,
        subject_ready=subject_ready,
        topic_family_ready=family_ready,
    )
