from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class JobManifest:
    run_id: str
    path: Path
    created_at: str
    status: str = "running"
    stages: dict[str, dict[str, Any]] = field(default_factory=dict)
    selected: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    upload_ids: dict[str, str] = field(default_factory=dict)
    failure: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "status": self.status,
            "stages": self.stages,
            "selected": self.selected,
            "outputs": self.outputs,
            "upload_ids": self.upload_ids,
            "failure": self.failure,
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                delete=False,
            ) as handle:
                handle.write(payload)
                temp_path = Path(handle.name)
            os.replace(temp_path, self.path)
        except OSError as exc:
            raise RuntimeError(f"Could not write job manifest: {self.path}") from exc

    def checkpoint(self, stage: str, *, outputs: dict[str, str] | None = None) -> None:
        self.stages[stage] = {"status": "complete"}
        if outputs:
            self.outputs.update(outputs)
        self.failure = None
        self.save()

    def fail(self, stage: str, exc: Exception) -> None:
        self.status = "failed"
        self.failure = {
            "stage": stage,
            "error": str(exc),
        }
        self.stages[stage] = {"status": "failed", "error": str(exc)}
        self.save()

    def complete(self) -> None:
        self.status = "complete"
        self.failure = None
        self.save()


def new_manifest(path: str | Path, run_id: str) -> JobManifest:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest = JobManifest(
        run_id=run_id,
        path=Path(path),
        created_at=now,
    )
    manifest.save()
    return manifest


def load_manifest(path: str | Path) -> JobManifest:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise RuntimeError(f"job manifest does not exist: {manifest_path}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read job manifest: {manifest_path}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("job manifest must contain a JSON object")

    try:
        manifest = JobManifest(
            run_id=str(data["run_id"]),
            path=manifest_path,
            created_at=str(data["created_at"]),
            status=str(data.get("status", "running")),
            stages=dict(data.get("stages", {})),
            selected=dict(data.get("selected", {})),
            outputs=dict(data.get("outputs", {})),
            upload_ids=dict(data.get("upload_ids", {})),
            failure=data.get("failure"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("job manifest contains invalid data") from exc

    if manifest.status not in {"running", "complete", "failed"}:
        raise RuntimeError("job manifest contains invalid status")

    if manifest.failure is not None and not isinstance(manifest.failure, dict):
        raise RuntimeError("job manifest failure must be an object or null")

    return manifest


def stage_complete(manifest: JobManifest, stage: str) -> bool:
    return manifest.stages.get(stage, {}).get("status") == "complete"


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            delete=False,
        ) as handle:
            handle.write(data)
            temp_path = Path(handle.name)
        os.replace(temp_path, target)
    except OSError as exc:
        raise RuntimeError(f"Could not write artifact: {target}") from exc


def read_json(path: str | Path) -> Any:
    target = Path(path)
    if not target.exists():
        raise RuntimeError(f"artifact does not exist: {target}")
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read artifact: {target}") from exc
