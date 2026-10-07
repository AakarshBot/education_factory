from channel_history import HistoryEntry
from subject_analysis import CORE_SUBJECTS, MIN_COMPARISON_SAMPLES, analyze_subjects


def entry(subject, video_id, *, views, watch=10, avp=60, likes=1, comments=1, subs=1):
    return HistoryEntry(
        exam="SSC",
        subject=subject,
        topic=f"{subject} topic {video_id}",
        lesson_type="practice",
        title=f"{subject} lesson {video_id}",
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


def test_analyze_subjects_returns_all_core_subjects():
    results = analyze_subjects(
        [
            entry("Maths", "m1", views=100),
            entry("math", "m2", views=200),
            entry("math", "m3", views=900),
            entry("Reasoning", "r1", views=300),
        ]
    )

    assert tuple(item.subject for item in results) == CORE_SUBJECTS
    maths = results[0]
    reasoning = results[1]
    english = results[2]

    assert maths.measured_videos == 3
    assert maths.total_views == 1200
    assert maths.median_views == 200
    assert maths.comparison_ready is True

    assert reasoning.measured_videos == 1
    assert reasoning.comparison_ready is False

    assert english.measured_videos == 0
    assert english.comparison_ready is False


def test_analyze_subjects_excludes_scheduled_and_non_core_subjects():
    results = analyze_subjects(
        [
            entry("Maths", "m1", views=100),
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
            entry("Geography", "g1", views=500),
        ]
    )

    assert results[0].measured_videos == 1
    assert results[0].total_views == 100
    assert results[2].measured_videos == 0


def test_analyze_subjects_calculates_rates_from_totals():
    entries = [
        entry("Reasoning", "r1", views=100, likes=10, comments=5, subs=2),
        entry("Reasoning", "r2", views=300, likes=20, comments=10, subs=4),
    ]

    result = analyze_subjects(entries)[1]

    assert result.engagement_rate_percent == 45 / 400 * 100
    assert result.subscribers_per_1000_views == 6 / 400 * 1000


def test_analyze_subjects_handles_empty_history():
    results = analyze_subjects([])
    assert len(results) == 3
    assert all(item.measured_videos == 0 for item in results)
    assert all(item.comparison_ready is False for item in results)


def test_analyze_subjects_requires_three_measured_videos():
    result = analyze_subjects(
        [
            entry("English", "e1", views=100),
            entry("English", "e2", views=200),
        ]
    )[2]

    assert result.measured_videos == 2
    assert result.comparison_ready is False
    assert MIN_COMPARISON_SAMPLES == 3


def test_analyze_subjects_excludes_shorts():
    short = entry("Maths", "s1", views=999)
    short = __import__("dataclasses").replace(short, content_format="shorts")
    assert analyze_subjects([short])[0].measured_videos == 0
