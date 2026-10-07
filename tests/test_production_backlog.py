from datetime import datetime, timezone

import pytest

from editorial_queue import EditorialJob
from production_backlog import (
    BacklogEntry,
    claim_job,
    complete_job,
    load_backlog,
    merge_jobs,
    pending_jobs,
    release_stale_claims,
    save_backlog,
)


def job(topic: str, score: float, priority: int = 1) -> EditorialJob:
    return EditorialJob(
        priority=priority,
        exam="SSC",
        subject="Maths",
        topic=topic,
        total_score=score,
        supporting_signal_indices=(0,),
        rationale=f"reason for {topic}",
    )


def test_backlog_round_trip(tmp_path):
    path = tmp_path / "backlog.json"
    entries = merge_jobs([], [job("Percentages", 90)])

    save_backlog(entries, path)

    loaded = load_backlog(path)
    assert loaded == entries
    assert pending_jobs(loaded)[0].topic == "Percentages"


def test_merge_refreshes_pending_duplicate_and_keeps_claimed_duplicate():
    initial = merge_jobs([], [job("Percentages", 70)])
    refreshed = merge_jobs(initial, [job("Percentages", 95)])
    assert len(refreshed) == 1
    assert refreshed[0].total_score == 95

    claimed = claim_job(refreshed, refreshed[0].to_job(), run_id="run-1")
    kept = merge_jobs(claimed, [job("Percentages", 100)])
    assert len(kept) == 1
    assert kept[0].status == "claimed"
    assert kept[0].total_score == 95


def test_claim_and_complete_job():
    entries = merge_jobs([], [job("Percentages", 90), job("Ratio", 80)])
    selected = pending_jobs(entries)[0]

    claimed = claim_job(entries, selected, run_id="run-1")
    claimed_entry = next(entry for entry in claimed if entry.key == selected_key(selected))
    assert claimed_entry.status == "claimed"
    assert claimed_entry.claimed_run_id == "run-1"

    completed = complete_job(
        claimed,
        exam=selected.exam,
        subject=selected.subject,
        topic=selected.topic,
        run_id="run-1",
    )
    assert [entry.topic for entry in completed] == ["Ratio"]


def test_complete_job_is_idempotent_after_already_removed():
    entries = merge_jobs([], [job("Percentages", 90)])
    selected = pending_jobs(entries)[0]
    claimed = claim_job(entries, selected, run_id="run-1")
    completed = complete_job(
        claimed,
        exam="SSC",
        subject="Maths",
        topic="Percentages",
        run_id="run-1",
    )
    assert complete_job(
        completed,
        exam="SSC",
        subject="Maths",
        topic="Percentages",
        run_id="run-1",
    ) == []


def test_claimed_job_requires_same_run_to_complete():
    entries = merge_jobs([], [job("Percentages", 90)])
    claimed = claim_job(entries, pending_jobs(entries)[0], run_id="run-1")

    with pytest.raises(RuntimeError, match="not claimed by run"):
        complete_job(
            claimed,
            exam="SSC",
            subject="Maths",
            topic="Percentages",
            run_id="run-2",
        )


def test_stale_claims_are_released():
    base = merge_jobs(
        [],
        [job("Percentages", 90)],
        now=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )
    claimed = claim_job(
        base,
        pending_jobs(base)[0],
        run_id="run-1",
        now=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )

    fresh = release_stale_claims(
        claimed,
        now=datetime(2026, 10, 2, tzinfo=timezone.utc),
        max_age_hours=48,
    )
    assert fresh[0].status == "claimed"

    stale = release_stale_claims(
        claimed,
        now=datetime(2026, 10, 4, tzinfo=timezone.utc),
        max_age_hours=48,
    )
    assert stale[0].status == "pending"
    assert stale[0].claimed_run_id is None


def test_save_backlog_replaces_file_atomically(tmp_path):
    path = tmp_path / "backlog.json"
    save_backlog(merge_jobs([], [job("Percentages", 90)]), path)
    first = path.read_text(encoding="utf-8")
    save_backlog(merge_jobs([], [job("Ratio", 80)]), path)
    second = path.read_text(encoding="utf-8")
    assert "Percentages" in first
    assert "Ratio" in second


def selected_key(item: EditorialJob) -> tuple[str, str, str]:
    return (
        item.exam.strip().lower(),
        item.subject.strip().lower(),
        item.topic.strip().lower(),
    )
