from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from factory_state import (
    FactoryState,
    load_state,
    next_run_at,
    record_run,
    save_state,
)


def test_default_state(tmp_path):
    assert load_state(tmp_path / "missing-state.json") == FactoryState()


def test_state_round_trip(tmp_path):
    path = tmp_path / "state.json"
    state = record_run(
        FactoryState(),
        run_id="run-1",
        status="complete",
        now=datetime(2026, 10, 8, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
        runs_per_day=2,
    )

    save_state(state, path)

    assert load_state(path) == state


def test_next_run_is_twelve_hours_for_two_runs():
    now = datetime(2026, 10, 8, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert next_run_at(now, 2) == datetime(2026, 10, 8, 18, 30, tzinfo=ZoneInfo("UTC"))


def test_next_run_is_one_day_for_one_run():
    now = datetime(2026, 10, 8, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert next_run_at(now, 1) == datetime(2026, 10, 9, 6, 30, tzinfo=ZoneInfo("UTC"))


def test_invalid_cadence():
    with pytest.raises(ValueError, match="1 or 2"):
        next_run_at(datetime.now(timezone.utc), 3)


def test_naive_datetime_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        next_run_at(datetime(2026, 10, 8, 12, 0), 2)


def test_run_id_and_status_are_required():
    with pytest.raises(ValueError, match="run_id"):
        record_run(
            FactoryState(),
            run_id="",
            status="complete",
            now=datetime.now(timezone.utc),
            runs_per_day=2,
        )
    with pytest.raises(ValueError, match="status"):
        record_run(
            FactoryState(),
            run_id="run-1",
            status="",
            now=datetime.now(timezone.utc),
            runs_per_day=2,
        )
