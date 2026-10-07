from channel_history import HistoryEntry
from topic_family_analysis import MIN_COMPARISON_SAMPLES, analyze_topic_families


def entry(subject, topic, video_id, *, views, watch=10, avp=60, likes=1, comments=1, subs=1):
    return HistoryEntry(
        exam="SSC",
        subject=subject,
        topic=topic,
        lesson_type="practice",
        title=f"{topic} lesson {video_id}",
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


def test_analyze_topic_families_clusters_related_topics_within_subject():
    entries = [
        entry("Maths", "Percentages", "p1", views=100),
        entry("Maths", "Percentage shortcuts", "p2", views=200),
        entry("Maths", "Percentages questions", "p3", views=900),
        entry("Maths", "Simple Interest", "s1", views=500),
    ]

    results = analyze_topic_families(entries)

    percentage = next(item for item in results if item.family_name == "Percentages")
    interest = next(item for item in results if item.family_name == "Simple Interest")

    assert percentage.topic_count == 3
    assert percentage.measured_videos == 3
    assert percentage.median_views == 200
    assert percentage.comparison_ready is True
    assert set(percentage.topics) == {
        "Percentages",
        "Percentage shortcuts",
        "Percentages questions",
    }

    assert interest.topic_count == 1
    assert interest.measured_videos == 1
    assert interest.comparison_ready is False


def test_analyze_topic_families_normalizes_plural_topic_tokens():
    results = analyze_topic_families(
        [
            entry("Maths", "Percentage", "p1", views=100),
            entry("Maths", "Percentages", "p2", views=200),
            entry("Maths", "Percentage shortcuts", "p3", views=300),
        ]
    )

    assert len(results) == 1
    assert results[0].topic_count == 3
    assert results[0].measured_videos == 3


def test_analyze_topic_families_keeps_subjects_separate():
    entries = [
        entry("Maths", "Time and Work", "m1", views=100),
        entry("Reasoning", "Time and Work", "r1", views=900),
    ]

    results = analyze_topic_families(entries)

    assert len(results) == 2
    assert {item.subject for item in results} == {"maths", "reasoning"}


def test_analyze_topic_families_excludes_scheduled_and_empty_topics():
    entries = [
        entry("English", "Error Spotting", "e1", views=100),
        HistoryEntry(
            exam="SSC",
            subject="English",
            topic="Grammar",
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
            subject="English",
            topic="",
            lesson_type="practice",
            title="Empty",
            status="published",
            created_at="2026-10-01T00:00:00Z",
            video_id="e2",
            published_at="2026-10-01T00:00:00Z",
            metrics={"views": 500},
        ),
    ]

    results = analyze_topic_families(entries)
    assert len(results) == 1
    assert results[0].family_name == "Error Spotting"
    assert results[0].measured_videos == 1


def test_analyze_topic_families_calculates_rates():
    entries = [
        entry("Reasoning", "Syllogism", "s1", views=100, likes=10, comments=5, subs=2),
        entry("Reasoning", "Syllogism shortcuts", "s2", views=300, likes=20, comments=10, subs=4),
    ]

    result = analyze_topic_families(entries)[0]
    assert result.engagement_rate_percent == 45 / 400 * 100
    assert result.subscribers_per_1000_views == 6 / 400 * 1000


def test_analyze_topic_families_flags_small_samples():
    result = analyze_topic_families(
        [
            entry("English", "Cloze Test", "c1", views=100),
            entry("English", "Cloze Test shortcut", "c2", views=200),
        ]
    )[0]
    assert result.measured_videos == 2
    assert result.comparison_ready is False
    assert MIN_COMPARISON_SAMPLES == 3


def test_analyze_topic_families_empty_history():
    assert analyze_topic_families([]) == tuple()
