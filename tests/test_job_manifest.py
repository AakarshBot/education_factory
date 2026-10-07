from pathlib import Path

import pytest

from job_manifest import (
    JobManifest,
    load_manifest,
    new_manifest,
    stage_complete,
)


def test_new_manifest_round_trips(tmp_path):
    path = tmp_path / "job.json"
    manifest = new_manifest(path, "20261007-230000")
    manifest.selected["topic"] = "Percentages"
    manifest.outputs["questions"] = "questions.json"
    manifest.checkpoint("questions", outputs={"questions": "questions.json"})

    loaded = load_manifest(path)
    assert loaded.run_id == "20261007-230000"
    assert loaded.selected["topic"] == "Percentages"
    assert loaded.outputs["questions"] == "questions.json"
    assert stage_complete(loaded, "questions")


def test_manifest_records_failure_and_can_resume(tmp_path):
    path = tmp_path / "job.json"
    manifest = new_manifest(path, "run")
    manifest.fail("render", RuntimeError("ffmpeg failed"))

    loaded = load_manifest(path)
    assert loaded.status == "failed"
    assert loaded.failure == {"stage": "render", "error": "ffmpeg failed"}
    assert stage_complete(loaded, "questions") is False


def test_manifest_complete_clears_failure(tmp_path):
    path = tmp_path / "job.json"
    manifest = new_manifest(path, "run")
    manifest.fail("metadata", RuntimeError("bad metadata"))
    manifest.complete()

    loaded = load_manifest(path)
    assert loaded.status == "complete"
    assert loaded.failure is None


def test_load_manifest_rejects_missing_file(tmp_path):
    with pytest.raises(RuntimeError, match="does not exist"):
        load_manifest(tmp_path / "missing.json")


def test_load_manifest_rejects_invalid_json(tmp_path):
    path = tmp_path / "job.json"
    path.write_text("{bad", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Could not read"):
        load_manifest(path)


def test_checkpoint_is_atomic_enough_for_normal_resume(tmp_path):
    path = tmp_path / "nested" / "job.json"
    manifest = new_manifest(path, "run")
    manifest.checkpoint("selection")
    assert Path(path).exists()
