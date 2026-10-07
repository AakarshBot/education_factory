import factory
from channel_history import HistoryEntry


def _entry(topic, lesson_type="practice", subject="Maths"):
    return HistoryEntry(
        exam="SSC",
        subject=subject,
        topic=topic,
        lesson_type=lesson_type,
        title=f"{topic} practice",
        status="published",
        created_at="2026-10-01T00:00:00Z",
        video_id=f"id-{topic}",
        published_at="2026-10-01T00:00:00Z",
        metrics={
            "views": 100,
            "estimatedMinutesWatched": 50,
            "averageViewPercentage": 60,
            "likes": 5,
            "comments": 1,
            "subscribersGained": 2,
        },
    )


def test_select_lesson_type_prefers_supported_adapted_format():
    class Adaptation:
        format_weights = {"practice": 0.9, "timed_test": 1.1, "revision": 1.0}

    assert factory._select_lesson_type(Adaptation()) == "timed_test"


def test_select_lesson_type_keeps_practice_as_neutral_default():
    class Adaptation:
        format_weights = {}

    assert factory._select_lesson_type(Adaptation()) == "practice"


def test_next_publish_time_uses_next_local_six_pm():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    zone = ZoneInfo("Asia/Kolkata")
    now = datetime(2026, 10, 7, 17, 0, tzinfo=zone)
    assert factory._next_publish_time(now) == datetime(2026, 10, 7, 18, 0, tzinfo=zone)

    now = datetime(2026, 10, 7, 19, 0, tzinfo=zone)
    assert factory._next_publish_time(now) == datetime(2026, 10, 8, 18, 0, tzinfo=zone)


def test_scene_durations_cover_audio_exactly():
    durations = factory._scene_durations(["one two", "three", "four five six"], 6.0)
    assert round(sum(durations), 6) == 6.0
    assert all(duration > 0 for duration in durations)


def test_factory_runs_stages_in_order(monkeypatch, tmp_path):
    class Question:
        pass

    class Lesson:
        title = "SSC Maths Percentages"
        subject = "Maths"
        exam = "SSC"
        topic = "Percentages"

    calls = []

    monkeypatch.setattr(factory, "load_history", lambda path: calls.append("history") or [])
    monkeypatch.setattr(factory, "analyze_formats", lambda history: calls.append("formats") or ())
    monkeypatch.setattr(factory, "analyze_subjects", lambda history: calls.append("subjects") or ())
    monkeypatch.setattr(factory, "analyze_topic_families", lambda history: calls.append("families") or ())

    class Adaptation:
        format_weights = {"practice": 1.0, "timed_test": 1.0, "revision": 1.0}
        subject_weights = {"maths": 1.0}

    monkeypatch.setattr(factory, "build_editorial_adaptation", lambda *args: calls.append("adaptation") or Adaptation())

    monkeypatch.setattr(factory, "discover_demand", lambda: calls.append("demand") or ["signal"])
    monkeypatch.setattr(factory, "score_topics", lambda *args, **kwargs: calls.append("score") or ["score"])

    class Job:
        priority = 1
        total_score = 100
        subject = "Maths"
        exam = "SSC"
        topic = "Percentages"

    monkeypatch.setattr(factory, "build_editorial_queue", lambda *args, **kwargs: calls.append("queue") or [Job()])
    monkeypatch.setattr(factory, "generate_questions", lambda **kwargs: calls.append("questions") or [Question()])
    monkeypatch.setattr(factory, "generate_explanations", lambda questions, language: calls.append("explanations") or questions)
    monkeypatch.setattr(factory, "assemble_lesson", lambda questions, lesson_type: calls.append("lesson") or Lesson())
    monkeypatch.setattr(factory, "_narration_segments", lambda lesson: calls.append("narration_segments") or ["Question text"])
    monkeypatch.setattr(factory, "synthesize_speech", lambda *args, **kwargs: calls.append("tts") or tmp_path / "narration.mp3")

    class AudioResult:
        duration_seconds = 2.0

    monkeypatch.setattr(factory, "check_audio", lambda *args, **kwargs: calls.append("audio_qa") or AudioResult())
    monkeypatch.setattr(factory, "_scene_durations", lambda *args: calls.append("durations") or [2.0])
    monkeypatch.setattr(factory, "render_long_form", lambda *args, **kwargs: calls.append("render") or tmp_path / "video.mp4")
    monkeypatch.setattr(factory, "generate_metadata", lambda *args, **kwargs: calls.append("metadata") or type("Meta", (), {"to_dict": lambda self: {}})())
    monkeypatch.setattr(factory, "get_youtube_client", lambda: calls.append("auth") or object())
    monkeypatch.setattr(factory, "_next_publish_time", lambda now: None)
    monkeypatch.setattr(factory, "upload_video", lambda *args, **kwargs: calls.append("upload") or "video-id")
    monkeypatch.setattr(factory, "ingest_metrics", lambda **kwargs: calls.append("analytics") or [])

    lesson = factory.run_factory(output_root=tmp_path, history_path=tmp_path / "history.json")
    assert lesson.title == "SSC Maths Percentages"
    assert calls == [
        "history",
        "formats",
        "subjects",
        "families",
        "adaptation",
        "demand",
        "score",
        "queue",
        "questions",
        "explanations",
        "lesson",
        "narration_segments",
        "tts",
        "audio_qa",
        "durations",
        "render",
        "metadata",
        "auth",
        "upload",
        "analytics",
    ]


def test_short_segment_indices_selects_one_question_cycle():
    class Segment:
        def __init__(self, kind):
            self.kind = kind

    class Lesson:
        segments = tuple(Segment(kind) for kind in (
            "question", "answer", "explanation",
            "shortcut", "question", "answer",
        ))

    assert factory._short_segment_indices(Lesson()) == [0, 1, 2, 3]


def test_short_segment_indices_requires_question():
    class Lesson:
        segments = ()

    import pytest
    with pytest.raises(RuntimeError, match="no question"):
        factory._short_segment_indices(Lesson())
