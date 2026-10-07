from channel_history import HistoryEntry
from format_analysis import MIN_COMPARISON_SAMPLES, analyze_formats


def entry(lesson_type, video_id, *, views, watch=10, avp=60, likes=1, comments=1, subs=1):
    return HistoryEntry(
        exam="SSC",
        subject="Maths",
        topic=f"{lesson_type} topic {video_id}",
        lesson_type=lesson_type,
        title=f"{lesson_type} lesson {video_id}",
        status="published",
        created_at="2026-10-01T00:00:00Z",
        video_id=video_id,
        published_at="2026-10-01T00:00:00Z",
        metrics={
            "views": views,
            "estimatedMinutesWatched": watch,
            "averageViewDuration": 60,
            "averageViewPercentage": avp,
            "likes": likes,
            "comments": comments,
            "subscribersGained": subs,
        },
    )


def test_analyze_formats_groups_and_uses_medians():
    entries = [
        entry("practice", "p1", views=100, watch=10),
        entry("practice", "p2", views=200, watch=20),
        entry("practice", "p3", views=1000, watch=100),
        entry("timed_test", "t1", views=500, watch=50),
    ]

    results = analyze_formats(entries)

    practice = results[0]
    timed = results[1]

    assert practice.lesson_type == "practice"
    assert practice.measured_videos == 3
    assert practice.total_views == 1300
    assert practice.average_views == 1300 / 3
    assert practice.median_views == 200
    assert practice.total_watch_minutes == 130
    assert practice.median_watch_minutes == 20
    assert practice.comparison_ready is True

    assert timed.lesson_type == "timed_test"
    assert timed.measured_videos == 1
    assert timed.comparison_ready is False


def test_analyze_formats_excludes_scheduled_and_unmeasured_entries():
    entries = [
        entry("practice", "p1", views=100),
        HistoryEntry(
            exam="SSC",
            subject="Maths",
            topic="scheduled",
            lesson_type="practice",
            title="Scheduled",
            status="scheduled",
            created_at="2026-10-01T00:00:00Z",
            video_id="s1",
            published_at=None,
            metrics={"views": 999},
        ),
        HistoryEntry(
            exam="SSC",
            subject="Maths",
            topic="no-metrics",
            lesson_type="practice",
            title="No metrics",
            status="published",
            created_at="2026-10-01T00:00:00Z",
            video_id="n1",
            published_at="2026-10-01T00:00:00Z",
            metrics={},
        ),
    ]

    result = analyze_formats(entries)[0]
    assert result.measured_videos == 1
    assert result.total_views == 100


def test_analyze_formats_calculates_rates_from_totals():
    entries = [
        entry("practice", "p1", views=100, likes=10, comments=5, subs=2),
        entry("practice", "p2", views=300, likes=20, comments=10, subs=4),
    ]

    result = analyze_formats(entries)[0]

    assert result.engagement_rate_percent == 45 / 400 * 100
    assert result.subscribers_per_1000_views == 6 / 400 * 1000


def test_analyze_formats_normalizes_concept_name():
    result = analyze_formats(
        [entry("concept + practice", "c1", views=100)]
    )[0]
    assert result.lesson_type == "concept_practice"


def test_analyze_formats_empty_history():
    assert analyze_formats([]) == tuple()


def test_analyze_formats_flags_small_samples():
    entries = [
        entry("revision", "r1", views=100),
        entry("revision", "r2", views=200),
    ]
    result = analyze_formats(entries)[0]
    assert result.measured_videos == 2
    assert result.comparison_ready is False
    assert MIN_COMPARISON_SAMPLES == 3
