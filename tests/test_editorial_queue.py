import pytest

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


def test_queue_rejects_invalid_input():
    with pytest.raises(ValueError, match="must not be empty"):
        build_editorial_queue([])

    with pytest.raises(ValueError, match="at least 1"):
        build_editorial_queue([make_score()], max_jobs=0)
