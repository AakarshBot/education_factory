from adaptation import (
    MAX_WEIGHT,
    MIN_WEIGHT,
    MIN_READY_GROUPS,
    build_editorial_adaptation,
)
from format_analysis import FormatPerformance
from subject_analysis import SubjectPerformance
from topic_family_analysis import TopicFamilyPerformance


def format_item(name, median_views, count=3, ready=True):
    return FormatPerformance(
        lesson_type=name,
        measured_videos=count,
        total_views=median_views * count,
        average_views=median_views,
        median_views=median_views,
        total_watch_minutes=60,
        average_watch_minutes=20,
        median_watch_minutes=20,
        average_view_percentage=70,
        engagement_rate_percent=5,
        subscribers_per_1000_views=10,
        comparison_ready=ready,
    )


def subject_item(name, median_views, count=3, ready=True):
    return SubjectPerformance(
        subject=name,
        measured_videos=count,
        total_views=median_views * count,
        average_views=median_views,
        median_views=median_views,
        total_watch_minutes=60,
        average_watch_minutes=20,
        median_watch_minutes=20,
        average_view_percentage=70,
        engagement_rate_percent=5,
        subscribers_per_1000_views=10,
        comparison_ready=ready,
    )


def family_item(subject, name, median_views, count=3, ready=True):
    return TopicFamilyPerformance(
        subject=subject,
        family_name=name,
        topics=(name,),
        topic_count=1,
        measured_videos=count,
        total_views=median_views * count,
        average_views=median_views,
        median_views=median_views,
        total_watch_minutes=60,
        average_watch_minutes=20,
        median_watch_minutes=20,
        average_view_percentage=70,
        engagement_rate_percent=5,
        subscribers_per_1000_views=10,
        comparison_ready=ready,
    )


def test_adaptation_requires_two_ready_groups():
    result = build_editorial_adaptation(
        [format_item("practice", 100)],
        [subject_item("maths", 100)],
        [family_item("maths", "Percentages", 100)],
    )

    assert result.format_ready is False
    assert result.subject_ready is False
    assert result.topic_family_ready is False
    assert result.format_weights == {"practice": 1.0}


def test_adaptation_changes_ready_groups_conservatively():
    result = build_editorial_adaptation(
        [
            format_item("practice", 200),
            format_item("timed_test", 100),
            format_item("revision", 0),
        ],
        [
            subject_item("maths", 300),
            subject_item("reasoning", 100),
            subject_item("english", 100, count=2, ready=False),
        ],
        [
            family_item("maths", "Percentages", 300),
            family_item("maths", "Ratios", 100),
            family_item("english", "Error Spotting", 100, count=2, ready=False),
        ],
    )

    assert result.format_ready is True
    assert result.subject_ready is True
    assert result.topic_family_ready is True

    assert result.format_weights["practice"] > result.format_weights["timed_test"]
    assert result.format_weights["revision"] == 1.0
    assert result.subject_weights["maths"] > result.subject_weights["reasoning"]
    assert result.subject_weights["english"] == 1.0
    assert result.topic_family_weights[("maths", "Percentages")] > result.topic_family_weights[
        ("maths", "Ratios")
    ]
    assert all(
        MIN_WEIGHT <= value <= MAX_WEIGHT
        for value in result.format_weights.values()
    )


def test_adaptation_never_changes_weights_for_nonready_group():
    result = build_editorial_adaptation(
        [
            format_item("practice", 100, count=3),
            format_item("timed_test", 900, count=2, ready=False),
            format_item("revision", 500, count=3),
        ],
        [
            subject_item("maths", 100),
            subject_item("reasoning", 900),
        ],
        [],
    )

    assert result.format_weights["timed_test"] == 1.0
    assert result.topic_family_weights == {}


def test_adaptation_constants_are_conservative():
    assert MIN_READY_GROUPS == 2
    assert MAX_WEIGHT - MIN_WEIGHT == 0.20
