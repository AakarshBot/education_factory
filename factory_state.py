from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_STATE_FILE = Path("data/factory_state.json")
VALID_RUNS_PER_DAY = (1, 2)


@dataclass(frozen=True)
class FactoryState:
    last_run_at: str | None = None
    last_status: str | None = None
    last_run_id: str | None = None
    next_run_at: str | None = None
    runs_per_day: int = 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_run_at": self.last_run_at,
            "last_status": self.last_status,
            "last_run_id": self.last_run_id,
            "next_run_at": self.next_run_at,
            "runs_per_day": self.runs_per_day,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FactoryState":
        if not isinstance(data, dict):
            raise ValueError("factory state must be an object")
        runs_per_day = int(data.get("runs_per_day", 2))
        validate_runs_per_day(runs_per_day)
        return cls(
            last_run_at=data.get("last_run_at"),
            last_status=data.get("last_status"),
            last_run_id=data.get("last_run_id"),
            next_run_at=data.get("next_run_at"),
            runs_per_day=runs_per_day,
        )


def validate_runs_per_day(runs_per_day: int) -> None:
    if runs_per_day not in VALID_RUNS_PER_DAY:
        raise ValueError("runs_per_day must be 1 or 2")


def load_state(path: Path = DEFAULT_STATE_FILE) -> FactoryState:
    if not path.exists():
        return FactoryState()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read factory state: {path}") from exc

    try:
        return FactoryState.from_dict(data)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Factory state contains invalid data") from exc


def save_state(
    state: FactoryState,
    path: Path = DEFAULT_STATE_FILE,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(state.to_dict(), handle, ensure_ascii=False, indent=2)
            handle.flush()
            temp_path = Path(handle.name)
        temp_path.replace(path)
    except OSError as exc:
        raise RuntimeError(f"Could not write factory state: {path}") from exc


def next_run_at(now: datetime, runs_per_day: int) -> datetime:
    validate_runs_per_day(runs_per_day)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    reference = now.astimezone(timezone.utc)
    interval = timedelta(hours=24 / runs_per_day)
    return reference + interval


def record_run(
    state: FactoryState,
    *,
    run_id: str,
    status: str,
    now: datetime,
    runs_per_day: int,
) -> FactoryState:
    validate_runs_per_day(runs_per_day)
    if not run_id.strip():
        raise ValueError("run_id must not be empty")
    if not status.strip():
        raise ValueError("status must not be empty")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    timestamp = now.astimezone(timezone.utc)
    return FactoryState(
        last_run_at=timestamp.isoformat(),
        last_status=status.strip().lower(),
        last_run_id=run_id,
        next_run_at=next_run_at(timestamp, runs_per_day).isoformat(),
        runs_per_day=runs_per_day,
    )
