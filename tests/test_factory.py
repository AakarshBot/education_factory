import json
import math
import struct
import wave
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

import factory
from lesson import Lesson, LessonSegment
from metadata_generator import VideoMetadata
from topic_family_analysis import TopicFamilyPerformance
from question import Question


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


def test_record_publish_times_is_resume_stable(tmp_path):
    manifest = factory.new_manifest(tmp_path / "job.json", "run")
    zone = ZoneInfo("Asia/Kolkata")
    requested = datetime(2026, 10, 8, 18, 0, tzinfo=zone)

    first = factory._record_publish_times(
        manifest,
        publish_mode="scheduled",
        publish_at=requested,
    )
    assert first == (
        requested,
        datetime(2026, 10, 9, 6, 0, tzinfo=zone),
    )

    second = factory._record_publish_times(
        manifest,
        publish_mode="scheduled",
        publish_at=datetime(2026, 10, 9, 18, 0, tzinfo=zone),
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
