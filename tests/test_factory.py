import json
import math
import struct
import wave
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

import factory
from lesson import Lesson, LessonSegment
from metadata_generator import VideoMetadata
from topic_family_analysis import TopicFamilyPerformance
from question import Question
from editorial_queue import EditorialJob
from production_backlog import claim_job, load_backlog, merge_jobs, save_backlog


def question():
    return Question(
        subject="Maths",
        exam="SSC",
        topic="Percentages",
        difficulty="medium",
        question="25% of 200 is?",
        choices=("25", "50", "75", "100"),
        correct_answer="50",
        explanation="25% means one quarter, so 200 divided by 4 is 50.",
        shortcut=None,
        source_type="original",
        source_reference=None,
    )


def lesson():
    q = question()
    return Lesson(
        lesson_type="practice",
        title="SSC Maths Percentages Practice",
        subject="Maths",
        exam="SSC",
        topic="Percentages",
        questions=(q,),
        segments=(
            LessonSegment(kind="question", question_index=0),
            LessonSegment(kind="answer", question_index=0),
            LessonSegment(kind="explanation", question_index=0),
        ),
    )


def metadata():
    return VideoMetadata(
        primary_title="SSC Maths Percentages Practice",
        title_candidates=(
            "SSC Maths Percentages Practice",
            "Percentages Practice for SSC",
            "SSC Maths Percentage Questions",
            "Percentages Questions with Solutions",
            "SSC Percentage Practice",
        ),
        description="Practice percentages for SSC Maths.",
        hashtags=("#SSC", "#Maths", "#Percentages"),
        tags=("SSC Maths", "percentages"),
        series_context="SSC Maths Practice",
    )


def adaptation(weights=None):
    class Result:
        format_weights = weights if weights is not None else {
            "practice": 1.0,
            "timed_test": 1.0,
            "concept_practice": 1.0,
            "revision": 1.0,
        }
        subject_weights = {"maths": 1.0}

    return Result()




def test_explicit_editorial_job_normalizes_scope_without_fabricating_a_score():
    job = factory._explicit_editorial_job(
        "ssc",
        "maths",
        "Percentage and Successive Percentage Change",
    )

    assert job.exam == "SSC"
    assert job.subject == "Maths"
    assert job.topic == "Percentage and Successive Percentage Change"
    assert job.total_score == 0.0
    assert job.supporting_signal_indices == ()
    assert "no automatic demand score" in job.rationale


@pytest.mark.parametrize(
    ("exam", "subject", "topic"),
    [
        ("UPSC", "Maths", "Percentages"),
        ("SSC", "General Knowledge", "Percentages"),
        ("SSC", "Maths", " "),
        ("SSC", "Maths", "x" * 121),
    ],
)
def test_explicit_editorial_job_rejects_invalid_scope(exam, subject, topic):
    with pytest.raises(ValueError):
        factory._explicit_editorial_job(exam, subject, topic)


def test_factory_explicit_topic_override_skips_automatic_demand_selection(
    monkeypatch,
    tmp_path,
):
    generated = {}

    def fail_if_discovered():
        pytest.fail("explicit topic override must not run demand discovery")

    def stop_after_question_request(**kwargs):
        generated.update(kwargs)
        raise RuntimeError("stop after verifying editorial selection")

    monkeypatch.setattr(factory, "discover_demand", fail_if_discovered)
    monkeypatch.setattr(factory, "generate_questions", stop_after_question_request)

    with pytest.raises(RuntimeError, match="stop after verifying editorial selection"):
        factory.run_factory(
            output_root=tmp_path,
            history_path=tmp_path / "history.json",
            backlog_path=tmp_path / "backlog.json",
            factory_state_path=tmp_path / "factory_state.json",
            exam_override="ssc",
            subject_override="maths",
            topic_override="Percentage and Successive Percentage Change",
        )

    manifests = list((tmp_path / "jobs").glob("*/job.json"))
    assert len(manifests) == 1
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))

    assert manifest["status"] == "failed"
    assert manifest["failure"]["stage"] == "questions_generated"
    assert manifest["stages"]["editorial_selection"]["status"] == "complete"
    assert manifest["selected"]["selection_mode"] == "explicit_override"
    assert manifest["selected"]["exam"] == "SSC"
    assert manifest["selected"]["subject"] == "Maths"
    assert manifest["selected"]["topic"] == "Percentage and Successive Percentage Change"
    assert manifest["selected"]["lesson_type"] == "practice"
    assert "backlog_key" not in manifest["selected"]
    assert generated == {
        "exam": "SSC",
        "subject": "Maths",
        "topic": "Percentage and Successive Percentage Change",
        "difficulty": "mixed",
        "count": 10,
        "language": "Hinglish",
    }


def _recovery_job(topic):
    return EditorialJob(
        priority=1,
        exam="SSC",
        subject="Maths",
        topic=topic,
        total_score=90.0,
        supporting_signal_indices=(),
        rationale="test recovery queue item",
    )


def test_startup_recovery_closes_stale_job_and_removes_only_its_claim(tmp_path, capsys):
    now = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
    created = now - timedelta(hours=8)
    output_root = tmp_path / "output"
    manifest_path = output_root / "jobs" / "old-run" / "job.json"
    manifest = factory.new_manifest(manifest_path, "old-run")
    manifest.created_at = created.isoformat()
    manifest.selected["run_config"] = {"max_jobs": 10}
    manifest.selected["backlog_key"] = ["ssc", "maths", "percentages"]
    manifest.save()

    percentages = _recovery_job("Percentages")
    ratio = _recovery_job("Ratio")
    entries = merge_jobs([], [percentages, ratio], now=created)
    entries = claim_job(entries, percentages, run_id="old-run", now=created)
    entries = claim_job(entries, ratio, run_id="keep-run", now=created)
    backlog_path = tmp_path / "backlog.json"
    save_backlog(entries, backlog_path)

    recovery = factory._recover_interrupted_jobs(
        output_root,
        backlog_path,
        now=now,
        max_age_hours=6,
    )

    assert recovery is None
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved["status"] == "failed"
    assert saved["failure"]["stage"] == "automatic_stale_cleanup"
    assert saved["stages"]["automatic_stale_cleanup"]["status"] == "complete"
    remaining = load_backlog(backlog_path)
    assert len(remaining) == 1
    assert remaining[0].topic == "Ratio"
    assert remaining[0].claimed_run_id == "keep-run"
    assert "closed 1 abandoned job(s)" in capsys.readouterr().out


def test_factory_refuses_to_resume_cancelled_job(tmp_path):
    manifest_path = tmp_path / "jobs" / "cancelled-run" / "job.json"
    manifest = factory.new_manifest(manifest_path, "cancelled-run")
    manifest.selected["run_config"] = {"max_jobs": 10}
    manifest.save()
    manifest.fail("editorial_cancellation", RuntimeError("cancelled by editorial decision"))

    with pytest.raises(RuntimeError, match="cancelled or automatically closed"):
        factory.run_factory(resume=manifest_path)


def test_startup_recovery_returns_recent_failed_job_for_automatic_resume(tmp_path):
    now = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
    manifest_path = tmp_path / "output" / "jobs" / "retry-run" / "job.json"
    manifest = factory.new_manifest(manifest_path, "retry-run")
    manifest.created_at = (now - timedelta(hours=1)).isoformat()
    manifest.selected["run_config"] = {"max_jobs": 10}
    manifest.save()
    manifest.fail("long_render", RuntimeError("temporary render failure"))

    recovery = factory._recover_interrupted_jobs(
        tmp_path / "output",
        tmp_path / "backlog.json",
        now=now,
        max_age_hours=6,
    )

    assert recovery == manifest_path
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved["status"] == "failed"
    assert saved["failure"]["stage"] == "long_render"


def test_startup_recovery_never_resumes_cancelled_job_and_clears_its_claim(tmp_path):
    now = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
    manifest_path = tmp_path / "output" / "jobs" / "cancelled-run" / "job.json"
    manifest = factory.new_manifest(manifest_path, "cancelled-run")
    manifest.created_at = (now - timedelta(hours=1)).isoformat()
    manifest.selected["run_config"] = {"max_jobs": 10}
    manifest.save()
    manifest.fail("editorial_cancellation", RuntimeError("cancelled by editorial decision"))

    entry_job = _recovery_job("Cloze Test")
    entries = merge_jobs([], [entry_job], now=now)
    entries = claim_job(entries, entry_job, run_id="cancelled-run", now=now)
    backlog_path = tmp_path / "backlog.json"
    save_backlog(entries, backlog_path)

    recovery = factory._recover_interrupted_jobs(
        tmp_path / "output",
        backlog_path,
        now=now,
        max_age_hours=6,
    )

    assert recovery is None
    assert load_backlog(backlog_path) == []


def test_select_job_applies_topic_family_adaptation():
    class Job:
        def __init__(self, topic, score):
            self.priority = 1
            self.total_score = score
            self.subject = "Maths"
            self.exam = "SSC"
            self.topic = topic

    class Adaptation:
        subject_weights = {"maths": 1.0}
        topic_family_weights = {
            ("Maths", "Percentages"): 1.1,
            ("Maths", "Ratio"): 0.9,
        }

    families = (
        TopicFamilyPerformance(
            subject="Maths",
            family_name="Percentages",
            topics=("Percentages",),
            topic_count=1,
            measured_videos=3,
            total_views=300,
            average_views=100,
            median_views=100,
            total_watch_minutes=30,
            average_watch_minutes=10,
            median_watch_minutes=10,
            average_view_percentage=70,
            engagement_rate_percent=5,
            subscribers_per_1000_views=10,
            comparison_ready=True,
        ),
        TopicFamilyPerformance(
            subject="Maths",
            family_name="Ratio",
            topics=("Ratio",),
            topic_count=1,
            measured_videos=3,
            total_views=300,
            average_views=100,
            median_views=100,
            total_watch_minutes=30,
            average_watch_minutes=10,
            median_watch_minutes=10,
            average_view_percentage=70,
            engagement_rate_percent=5,
            subscribers_per_1000_views=10,
            comparison_ready=True,
        ),
    )

    selected = factory._select_job(
        [Job("Percentages", 100), Job("Ratio", 105)],
        Adaptation(),
        families,
    )
    assert selected.topic == "Percentages"

def test_select_lesson_type_respects_adaptation():
    result = adaptation({
        "practice": 0.9,
        "timed_test": 1.1,
        "concept_practice": 0.9,
        "revision": 0.9,
    })
    assert factory._select_lesson_type(result) == "timed_test"


def test_select_lesson_type_defaults_to_practice():
    assert factory._select_lesson_type(adaptation({})) == "practice"


def test_short_segment_indices_selects_one_question_cycle():
    assert factory._short_segment_indices(lesson()) == [0, 1, 2]


def test_short_segment_indices_requires_question():
    empty = Lesson(
        lesson_type="practice",
        title="Empty",
        subject="Maths",
        exam="SSC",
        topic="Test",
        questions=(),
        segments=(),
    )
    with pytest.raises(RuntimeError, match="no question"):
        factory._short_segment_indices(empty)


def test_next_publish_time_uses_10am_ist_before_slot():
    zone = ZoneInfo("Asia/Kolkata")
    now = datetime(2026, 10, 8, 9, 59, tzinfo=zone)

    assert factory._next_publish_time(now) == datetime(2026, 10, 8, 10, 0, tzinfo=zone)


def test_next_publish_time_after_slot_moves_to_next_day():
    zone = ZoneInfo("Asia/Kolkata")
    now = datetime(2026, 10, 8, 10, 1, tzinfo=zone)

    assert factory._next_publish_time(now) == datetime(2026, 10, 9, 10, 0, tzinfo=zone)


def test_record_publish_times_is_resume_stable(tmp_path):
    manifest = factory.new_manifest(tmp_path / "job.json", "run")
    zone = ZoneInfo("Asia/Kolkata")
    requested = datetime(2026, 10, 8, 10, 0, tzinfo=zone)

    first = factory._record_publish_times(
        manifest,
        publish_mode="scheduled",
        publish_at=requested,
    )
    assert first == (
        requested,
        datetime(2026, 10, 8, 18, 0, tzinfo=zone),
    )

    second = factory._record_publish_times(
        manifest,
        publish_mode="scheduled",
        publish_at=datetime(2026, 10, 9, 10, 0, tzinfo=zone),
    )
    assert second == first


def test_factory_resume_skips_completed_generation_and_audio(monkeypatch, tmp_path):
    render_state = {"fail": True}
    calls = {"questions": 0, "explanations": 0, "lesson": 0, "tts": 0, "tts_voices": []}

    class Job:
        priority = 1
        total_score = 100
        subject = "Maths"
        exam = "SSC"
        topic = "Percentages"
        rationale = "supported"
        supporting_signal_indices = (0,)

    monkeypatch.setattr(factory, "load_history", lambda path: [])
    monkeypatch.setattr(factory, "analyze_formats", lambda history: ())
    monkeypatch.setattr(factory, "analyze_subjects", lambda history: ())
    monkeypatch.setattr(factory, "analyze_topic_families", lambda history: ())
    monkeypatch.setattr(factory, "build_editorial_adaptation", lambda *args: adaptation())
    monkeypatch.setattr(factory, "discover_demand", lambda: ["signal"])
    monkeypatch.setattr(factory, "score_topics", lambda *args, **kwargs: ["score"])
    monkeypatch.setattr(factory, "build_editorial_queue", lambda *args, **kwargs: [Job()])
    monkeypatch.setattr(factory, "generate_questions", lambda **kwargs: calls.__setitem__("questions", calls["questions"] + 1) or [question()])
    monkeypatch.setattr(factory, "generate_english_narration_segments", lambda segments, source_language: list(segments))
    monkeypatch.setattr(factory, "generate_metadata", lambda lesson_value, language: metadata())
    monkeypatch.setattr(
        factory,
        "generate_explanations",
        lambda questions, language: calls.__setitem__("explanations", calls["explanations"] + 1) or questions,
    )
    monkeypatch.setattr(
        factory,
        "assemble_lesson",
        lambda questions, lesson_type, concept_summary=None: calls.__setitem__("lesson", calls["lesson"] + 1) or lesson(),
    )

    def fake_tts(text, output_path, **kwargs):
        calls["tts"] += 1
        calls["tts_voices"].append(kwargs.get("voice"))
        Path(output_path).write_bytes(b"audio")
        timing_path = kwargs.get("timing_path")
        if timing_path:
            Path(timing_path).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(factory, "synthesize_speech", fake_tts)
    monkeypatch.setattr(
        factory,
        "check_audio",
        lambda *args, **kwargs: type("Audio", (), {"duration_seconds": 2.0})(),
    )

    def fake_long_render(lesson_value, audio_path, output_path, durations):
        if render_state["fail"]:
            raise RuntimeError("render failed")
        Path(output_path).write_bytes(b"video")
        return Path(output_path)

    monkeypatch.setattr(factory, "render_long_form", fake_long_render)

    def fake_short_render(lesson_value, audio_path, output_path, indices, durations):
        Path(output_path).write_bytes(b"short")
        return Path(output_path)

    monkeypatch.setattr(factory, "render_short", fake_short_render)
    monkeypatch.setattr(factory, "generate_metadata", lambda *args, **kwargs: metadata())
    monkeypatch.setattr(factory, "get_youtube_client", lambda: object())
    monkeypatch.setattr(factory, "upload_video", lambda *args, **kwargs: "video-id")
    monkeypatch.setattr(factory, "ingest_metrics", lambda **kwargs: [])

    with pytest.raises(RuntimeError, match="render failed"):
        factory.run_factory(
            output_root=tmp_path,
            history_path=tmp_path / "history.json",
            backlog_path=tmp_path / "backlog.json",
            factory_state_path=tmp_path / "factory_state.json",
        )

    manifest_paths = list((tmp_path / "jobs").glob("*/job.json"))
    assert len(manifest_paths) == 1
    manifest_path = manifest_paths[0]
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved["status"] == "failed"
    assert saved["failure"]["stage"] == "long_render"
    assert saved["stages"]["questions_generated"]["status"] == "complete"
    assert saved["stages"]["long_narration"]["status"] == "complete"
    assert saved["selected"]["run_config"]["history_path"] == str((tmp_path / "history.json").resolve())
    assert saved["selected"]["run_config"]["backlog_path"] == str((tmp_path / "backlog.json").resolve())
    assert saved["selected"]["run_config"]["factory_state_path"] == str((tmp_path / "factory_state.json").resolve())
    assert saved["selected"]["run_config"]["runs_per_day"] == 2
    assert calls["questions"] == 1
    assert calls["explanations"] == 1
    assert calls["lesson"] == 1
    assert calls["tts"] == 1
    failed_state = json.loads((tmp_path / "factory_state.json").read_text(encoding="utf-8"))
    assert failed_state["last_status"] == "failed"
    assert failed_state["last_run_id"] == saved["run_id"]

    render_state["fail"] = False
    result = factory.run_factory(
        resume=manifest_path,
        history_path=tmp_path / "history.json",
        backlog_path=tmp_path / "backlog.json",
        factory_state_path=tmp_path / "factory_state.json",
    )

    assert result.title == "SSC Maths Percentages Practice"
    assert calls["questions"] == 1
    assert calls["explanations"] == 1
    assert calls["lesson"] == 1
    assert calls["tts"] == 4
    assert calls["tts_voices"] == [None, factory.ENGLISH_TTS_VOICE, None, factory.ENGLISH_TTS_VOICE]

    final = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert final["status"] == "complete"
    assert final["failure"] is None
    assert final["stages"]["english_metadata"]["status"] == "complete"
    assert final["stages"]["english_localization"]["status"] == "complete"
    assert final["stages"]["english_audio"]["status"] == "complete"
    assert final["stages"]["english_audio_qa"]["status"] == "complete"
    assert final["stages"]["english_short_audio"]["status"] == "complete"
    assert final["stages"]["english_short_audio_qa"]["status"] == "complete"
    assert final["stages"]["backlog_complete"]["status"] == "complete"
    state = json.loads((tmp_path / "factory_state.json").read_text(encoding="utf-8"))
    assert state["last_status"] == "complete"
    assert state["last_run_id"] == final["run_id"]
    assert state["runs_per_day"] == 2
    assert json.loads((tmp_path / "backlog.json").read_text(encoding="utf-8")) == []
    assert final["upload_ids"] == {
        "long_form": "video-id",
        "shorts": "video-id",
    }


def _write_test_audio(path: Path, duration: float = 1.0) -> None:
    rate = 8000
    frames = int(rate * duration)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        for index in range(frames):
            value = int(8000 * math.sin(2 * math.pi * 440 * index / rate))
            wav.writeframesraw(struct.pack("<h", value))


def test_factory_preflight_exercises_real_media_pipeline(monkeypatch, tmp_path):
    calls = {"tts": 0, "uploads": 0}

    class Job:
        priority = 1
        total_score = 100
        subject = "Maths"
        exam = "SSC"
        topic = "Percentages"
        rationale = "supported"
        supporting_signal_indices = (0,)

    monkeypatch.setattr(factory, "load_history", lambda path: [])
    monkeypatch.setattr(factory, "analyze_formats", lambda history: ())
    monkeypatch.setattr(factory, "analyze_subjects", lambda history: ())
    monkeypatch.setattr(factory, "analyze_topic_families", lambda history: ())
    monkeypatch.setattr(factory, "build_editorial_adaptation", lambda *args: adaptation())
    monkeypatch.setattr(factory, "discover_demand", lambda: ["signal"])
    monkeypatch.setattr(factory, "score_topics", lambda *args, **kwargs: ["score"])
    monkeypatch.setattr(factory, "build_editorial_queue", lambda *args, **kwargs: [Job()])
    monkeypatch.setattr(factory, "generate_questions", lambda **kwargs: [question()])
    monkeypatch.setattr(factory, "generate_explanations", lambda questions, language: questions)
    monkeypatch.setattr(factory, "assemble_lesson", lambda questions, lesson_type, concept_summary=None: lesson())
    monkeypatch.setattr(
        factory,
        "generate_english_narration_segments",
        lambda segments, source_language: list(segments),
    )
    monkeypatch.setattr(factory, "generate_metadata", lambda *args, **kwargs: metadata())

    def fake_tts(text, output_path, **kwargs):
        calls["tts"] += 1
        _write_test_audio(Path(output_path))
        timing_path = kwargs.get("timing_path")
        if timing_path:
            Path(timing_path).write_text(
                json.dumps({
                    "text": text,
                    "duration_seconds": 1.0,
                    "words": [
                        {
                            "text": word,
                            "start_seconds": index * 0.05,
                            "duration_seconds": 0.04,
                        }
                        for index, word in enumerate(text.split())
                    ],
                }),
                encoding="utf-8",
            )

    monkeypatch.setattr(factory, "synthesize_speech", fake_tts)
    monkeypatch.setattr(factory, "get_youtube_client", lambda: object())

    def fake_upload(*args, **kwargs):
        calls["uploads"] += 1
        return f"video-{calls['uploads']}"

    monkeypatch.setattr(factory, "upload_video", fake_upload)
    monkeypatch.setattr(factory, "ingest_metrics", lambda **kwargs: [])

    result = factory.run_factory(
        output_root=tmp_path,
        history_path=tmp_path / "history.json",
        backlog_path=tmp_path / "backlog.json",
        factory_state_path=tmp_path / "factory_state.json",
        question_count=1,
    )

    assert result.title == "SSC Maths Percentages Practice"
    assert calls["tts"] == 4
    assert calls["uploads"] == 2

    manifest_paths = list((tmp_path / "jobs").glob("*/job.json"))
    assert len(manifest_paths) == 1
    manifest = json.loads(manifest_paths[0].read_text(encoding="utf-8"))
    assert manifest["status"] == "complete"
    assert manifest["stages"]["long_render"]["status"] == "complete"
    assert manifest["stages"]["short_render"]["status"] == "complete"
    assert Path(manifest["outputs"]["long_video"]).exists()
    assert Path(manifest["outputs"]["short_video"]).exists()
