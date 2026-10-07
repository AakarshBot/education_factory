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
        format_weights = {
            "practice": 0.9,
            "timed_test": 1.1,
            "concept_practice": 1.0,
            "revision": 0.9,
        }

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

    narration_count = {"value": 0}
    def fake_narration_segments(lesson):
        calls.append("narration_segments")
        return ["Question text"]

    monkeypatch.setattr(factory, "_narration_segments", fake_narration_segments)

    def fake_tts(*args, **kwargs):
        narration_count["value"] += 1
        calls.append(f"tts{narration_count['value']}")
        return tmp_path / f"narration{narration_count['value']}.mp3"

    monkeypatch.setattr(factory, "synthesize_speech", fake_tts)

    class AudioResult:
        duration_seconds = 2.0

    monkeypatch.setattr(factory, "check_audio", lambda *args, **kwargs: calls.append("audio_qa") or AudioResult())
    monkeypatch.setattr(factory, "_scene_durations", lambda *args: calls.append("durations") or [2.0])

    monkeypatch.setattr(factory, "render_long_form", lambda *args, **kwargs: calls.append("render_long") or tmp_path / "video.mp4")
    monkeypatch.setattr(factory, "_short_segment_indices", lambda lesson: calls.append("short_select") or [0])
    monkeypatch.setattr(factory, "render_short", lambda *args, **kwargs: calls.append("render_short") or tmp_path / "short.mp4")

    class Metadata:
        primary_title = "Long"
        title_candidates = ("Long", "Short", "Three", "Four", "Five")
        description = "Description"
        hashtags = ("#SSC", "#Maths", "#Practice")
        tags = ("SSC Maths",)
        series_context = "SSC Maths Practice"
        category_id = "27"
        default_language = "hi"

        def to_dict(self):
            return {
                "primary_title": self.primary_title,
                "title_candidates": self.title_candidates,
                "description": self.description,
                "hashtags": self.hashtags,
                "tags": self.tags,
                "series_context": self.series_context,
                "category_id": self.category_id,
                "default_language": self.default_language,
            }

    monkeypatch.setattr(
        factory,
        "VideoMetadata",
        lambda **kwargs: Metadata(),
    )

    monkeypatch.setattr(factory, "generate_metadata", lambda *args, **kwargs: calls.append("metadata") or Metadata())
    monkeypatch.setattr(factory, "get_youtube_client", lambda: calls.append("auth") or object())
    monkeypatch.setattr(factory, "_next_publish_time", lambda now: None)

    def fake_upload(*args, **kwargs):
        calls.append("upload_short" if kwargs.get("content_format") == "shorts" else "upload_long")
        return "video-id"

    monkeypatch.setattr(factory, "upload_video", fake_upload)
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
        "tts1",
        "audio_qa",
        "durations",
        "render_long",
        "metadata",
        "short_select",
        "tts2",
        "audio_qa",
        "durations",
        "render_short",
        "auth",
        "upload_long",
        "upload_short",
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


def test_select_lesson_type_can_choose_concept_practice():
    class Adaptation:
        format_weights = {
            "practice": 0.9,
            "timed_test": 0.9,
            "concept_practice": 1.1,
            "revision": 0.9,
        }

    assert factory._select_lesson_type(Adaptation()) == "concept_practice"
