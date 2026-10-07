from datetime import datetime, timezone
from pathlib import Path

import pytest

from channel_history import (
    HistoryEntry,
    append_history,
    load_history,
    recent_topic_keys,
    save_history,
    topic_key,
)


def entry(
    topic="Percentages",
    *,
    status="published",
    created_at="2026-10-01T00:00:00Z",
):
    return HistoryEntry(
        exam="SSC",
        subject="Maths",
        topic=topic,
        lesson_type="practice",
        title=f"{topic} Practice",
        status=status,
        created_at=created_at,
        video_id=None,
        published_at=None,
        metrics={"views": 120.0},
    )


def test_missing_history_loads_empty(tmp_path):
    assert load_history(tmp_path / "history.json") == []


def test_history_round_trips(tmp_path):
    path = tmp_path / "history.json"
    original = [entry(), entry("Syllogism", status="scheduled")]

    save_history(original, path)

    assert load_history(path) == original


def test_append_history_preserves_existing_entries(tmp_path):
    path = tmp_path / "history.json"

    append_history(entry(), path)
    append_history(entry("Profit and Loss"), path)

    assert [item.topic for item in load_history(path)] == [
        "Percentages",
        "Profit and Loss",
    ]


def test_recent_topic_keys_include_only_active_recent_entries():
    now = datetime(2026, 10, 7, tzinfo=timezone.utc)
    entries = [
        entry("Percentages"),
        entry("Syllogism", status="scheduled"),
        entry("Old Topic", created_at="2026-08-01T00:00:00Z"),
        entry("Failed Topic", status="failed"),
    ]

    assert recent_topic_keys(entries, days=30, now=now) == {
        topic_key("SSC", "Maths", "Percentages"),
        topic_key("SSC", "Maths", "Syllogism"),
    }


def test_recent_topic_keys_rejects_invalid_window():
    with pytest.raises(ValueError, match="at least 1"):
        recent_topic_keys([], days=0)


def test_invalid_history_file_fails_closed(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("{not-json}", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Could not read"):
        load_history(path)

from channel_history import HistoryEntry, load_history, save_history


def test_history_defaults_content_format_to_long_form(tmp_path):
    path = tmp_path / "history.json"
    entry = HistoryEntry(
        exam="SSC",
        subject="Maths",
        topic="Percentages",
        lesson_type="practice",
        title="Practice",
        status="published",
        created_at="2026-10-01T00:00:00Z",
        metrics={"views": 10},
    )
    save_history([entry], path)
    loaded = load_history(path)
    assert loaded[0].content_format == "long_form"


def test_history_round_trips_shorts_format(tmp_path):
    path = tmp_path / "history.json"
    entry = HistoryEntry(
        exam="SSC",
        subject="Maths",
        topic="Percentages",
        lesson_type="practice",
        title="Short",
        status="published",
        created_at="2026-10-01T00:00:00Z",
        video_id="short1",
        metrics={"views": 10},
        content_format="shorts",
    )
    save_history([entry], path)
    loaded = load_history(path)
    assert loaded == [entry]
