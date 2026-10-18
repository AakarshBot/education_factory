from datetime import datetime, timezone

import pytest

from channel_history import HistoryEntry
from editorial_queue import build_editorial_queue
from topic_scorer import TopicScore


def make_score(
    exam="SSC",
    subject="Maths",
    topic="Percentages",
    total_score=90.0,
    signals=(0,),
):
    return TopicScore(
        exam=exam,
        subject=subject,
        topic=topic,
        demand_score=80.0,
        exam_relevance=90,
        novelty=50,
        educational_value=90,
        visual_potential=90,
        production_reliability=90,
        total_score=total_score,
        supporting_signal_indices=signals,
        rationale="Strong educational opportunity.",
    )


NOW = datetime(2026, 10, 19, 0, 0, tzinfo=timezone.utc)


def history(
    topic,
    status="published",
    *,
    exam="SSC",
    subject="Maths",
    created_at="2026-10-18T00:00:00Z",
):
    return HistoryEntry(
        exam=exam,
        subject=subject,
        topic=topic,
        lesson_type="practice",
        title=f"{topic} Practice",
        status=status,
        created_at=created_at,
    )


def test_queue_is_score_first_and_carries_evidence():
    scores = [
        make_score(topic="Profit and Loss", total_score=82.0, signals=(1,)),
        make_score(topic="Percentages", total_score=95.0, signals=(0,)),
    ]

    jobs = build_editorial_queue(scores, max_jobs=2)

    assert [job.priority for job in jobs] == [1, 2]
    assert [job.topic for job in jobs] == ["Percentages", "Profit and Loss"]
    assert jobs[0].supporting_signal_indices == (0,)
    assert jobs[0].rationale == "Strong educational opportunity."


def test_queue_respects_max_jobs():
    scores = [
        make_score(topic="A", total_score=90.0),
        make_score(topic="B", total_score=80.0),
        make_score(topic="C", total_score=70.0),
    ]

    jobs = build_editorial_queue(scores, max_jobs=2)

    assert [job.topic for job in jobs] == ["A", "B"]


def test_queue_has_deterministic_tie_breaking():
    scores = [
        make_score(subject="Reasoning", topic="Syllogism", total_score=90.0),
        make_score(subject="Maths", topic="Percentages", total_score=90.0),
    ]

    jobs = build_editorial_queue(scores, max_jobs=2)

    assert [(job.subject, job.topic) for job in jobs] == [
        ("Maths", "Percentages"),
        ("Reasoning", "Syllogism"),
    ]


def test_queue_deduplicates_exact_topic_keys():
    scores = [
        make_score(topic="Percentages", total_score=95.0),
        make_score(topic="percentages", total_score=94.0),
        make_score(topic="Profit and Loss", total_score=80.0),
    ]

    jobs = build_editorial_queue(scores, max_jobs=3)

    assert [job.topic for job in jobs] == ["Percentages", "Profit and Loss"]


def test_queue_skips_recent_published_topics():
    scores = [
        make_score(topic="Percentages", total_score=95.0),
        make_score(topic="Profit and Loss", total_score=80.0),
    ]

    jobs = build_editorial_queue(
        scores,
        history=[history("Percentages")],
        now=NOW,
    )

    assert [job.topic for job in jobs] == ["Profit and Loss"]



def test_queue_skips_recent_related_topic_but_keeps_distinct_option():
    scores = [
        make_score(
            exam="Banking",
            subject="English",
            topic="Error Detection",
            total_score=98.0,
        ),
        make_score(
            exam="Banking",
            subject="English",
            topic="Cloze Test",
            total_score=82.0,
        ),
    ]

    jobs = build_editorial_queue(
        scores,
        max_jobs=2,
        history=[
            history(
                "Advanced Error Detection",
                exam="Banking",
                subject="English",
            )
        ],
        now=NOW,
    )

    assert [job.topic for job in jobs] == ["Cloze Test"]


def test_queue_allows_related_topic_after_cooldown_expires():
    jobs = build_editorial_queue(
        [
            make_score(
                exam="Banking",
                subject="English",
                topic="Error Detection",
            )
        ],
        history=[
            history(
                "Advanced Error Detection",
                exam="Banking",
                subject="English",
                created_at="2026-10-01T00:00:00Z",
            )
        ],
        now=NOW,
    )

    assert [job.topic for job in jobs] == ["Error Detection"]


def test_queue_uses_related_topic_only_when_no_distinct_candidate_exists():
    jobs = build_editorial_queue(
        [
            make_score(
                exam="Banking",
                subject="English",
                topic="Error Detection",
                total_score=95.0,
            )
        ],
        history=[
            history(
                "Advanced Error Detection",
                exam="Banking",
                subject="English",
            )
        ],
        now=NOW,
    )

    assert [job.topic for job in jobs] == ["Error Detection"]
    assert "Fallback: no distinct eligible topic" in jobs[0].rationale


def test_queue_does_not_skip_failed_topics():
    jobs = build_editorial_queue(
        [make_score(topic="Percentages")],
        history=[history("Percentages", status="failed")],
    )

    assert [job.topic for job in jobs] == ["Percentages"]


def test_queue_rejects_invalid_input():
    with pytest.raises(ValueError, match="must not be empty"):
        build_editorial_queue([])

    with pytest.raises(ValueError, match="at least 1"):
        build_editorial_queue([make_score()], max_jobs=0)
