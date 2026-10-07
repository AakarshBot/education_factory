from datetime import datetime, timezone

import pytest

import youtube_uploader
from lesson import Lesson, LessonSegment
from metadata_generator import VideoMetadata
from question import Question


class FakeUploadRequest:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = 0

    def next_chunk(self):
        self.calls += 1
        if self.error:
            raise self.error
        return None, self.response


class FakeVideos:
    def __init__(self, response=None, error=None):
        self.body = None
        self.part = None
        self.media_body = None
        self.request = FakeUploadRequest(response=response, error=error)

    def insert(self, *, part, body, media_body):
        self.part = part
        self.body = body
        self.media_body = media_body
        return self.request


class FakeYouTube:
    def __init__(self, response=None, error=None):
        self.videos_api = FakeVideos(response=response, error=error)

    def videos(self):
        return self.videos_api


def lesson():
    question = Question(
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        difficulty="medium",
        question="25% of 240 is?",
        choices=("60", "70", "80", "90"),
        correct_answer="60",
        explanation="25 percent is one fourth.",
        shortcut="Divide by four.",
        source_type="original",
        source_reference=None,
    )
    return Lesson(
        lesson_type="practice",
        title="SSC CGL Maths Percentages Practice",
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        questions=(question,),
        segments=(
            LessonSegment(kind="question", question_index=0),
            LessonSegment(kind="answer", question_index=0),
        ),
    )


def metadata():
    return VideoMetadata(
        primary_title="SSC CGL Percentages Practice",
        title_candidates=(
            "SSC CGL Percentages Practice",
            "Percentages Practice for SSC CGL",
            "SSC CGL Maths Percentage Questions",
            "Master Percentages with SSC CGL",
            "SSC CGL Percentage Questions",
        ),
        description="Practice percentages for SSC CGL Maths.",
        hashtags=("#SSCCGL", "#SSCMaths", "#Percentages"),
        tags=("SSC CGL Maths", "percentages questions"),
        series_context="SSC Maths Practice",
    )


def english_metadata():
    return VideoMetadata(
        primary_title="SSC CGL Percentages Practice in English",
        title_candidates=(
            "SSC CGL Percentages Practice in English",
            "Percentages Practice for SSC CGL",
            "SSC CGL Maths Percentage Questions",
            "Master Percentages with SSC CGL Practice",
            "SSC CGL Percentage Questions",
        ),
        description="Practice percentages for SSC CGL Maths in clear English.",
        hashtags=("#SSCCGL", "#SSCMaths", "#Percentages"),
        tags=("SSC CGL Maths", "percentages questions"),
        series_context="SSC Maths Practice",
    )


def patch_media(monkeypatch):
    class FakeMediaFileUpload:
        def __init__(self, filename, **kwargs):
            self.filename = filename
            self.kwargs = kwargs

    monkeypatch.setattr(youtube_uploader, "MediaFileUpload", FakeMediaFileUpload)


def test_upload_public_video_uses_metadata_and_records_history(
    monkeypatch,
    tmp_path,
):
    patch_media(monkeypatch)
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")
    history = tmp_path / "history.json"
    youtube = FakeYouTube(response={"id": "video123"})

    result = youtube_uploader.upload_video(
        youtube,
        lesson(),
        metadata(),
        video,
        mode="public",
        history_path=history,
        now=datetime(2026, 10, 7, 12, tzinfo=timezone.utc),
        english_metadata=english_metadata(),
    )

    assert result == "video123"
    assert youtube.videos_api.part == "snippet,status,localizations"
    assert youtube.videos_api.body == {
        "snippet": {
            "title": "SSC CGL Percentages Practice",
            "description": (
                "Practice percentages for SSC CGL Maths.\n\n"
                "#SSCCGL #SSCMaths #Percentages"
            ),
            "tags": ["SSC CGL Maths", "percentages questions"],
            "categoryId": "27",
            "defaultLanguage": "hi",
            "defaultAudioLanguage": "hi",
        },
        "status": {"privacyStatus": "public"},
        "localizations": {
            "en": {
                "title": "SSC CGL Percentages Practice in English",
                "description": (
                    "Practice percentages for SSC CGL Maths in clear English.\n\n"
                    "#SSCCGL #SSCMaths #Percentages"
                ),
            }
        },
    }

    stored = history.read_text(encoding="utf-8")
    assert "video123" in stored
    assert '"status": "published"' in stored


def test_upload_scheduled_video_forces_private_and_sets_publish_at(
    monkeypatch,
    tmp_path,
):
    patch_media(monkeypatch)
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")
    history = tmp_path / "history.json"
    youtube = FakeYouTube(response={"id": "video456"})

    result = youtube_uploader.upload_video(
        youtube,
        lesson(),
        metadata(),
        video,
        mode="scheduled",
        publish_at=datetime(2026, 10, 8, 6, 30, tzinfo=timezone.utc),
        history_path=history,
        now=datetime(2026, 10, 7, 12, tzinfo=timezone.utc),
    )

    assert result == "video456"
    assert youtube.videos_api.body["status"] == {
        "privacyStatus": "private",
        "publishAt": "2026-10-08T06:30:00Z",
    }
    assert '"status": "scheduled"' in history.read_text(encoding="utf-8")
    assert '"published_at": "2026-10-08T06:30:00Z"' in history.read_text(
        encoding="utf-8"
    )


def test_upload_rejects_invalid_mode(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")
    with pytest.raises(ValueError, match="mode"):
        youtube_uploader.upload_video(
            FakeYouTube(response={"id": "x"}),
            lesson(),
            metadata(),
            video,
            mode="private",
        )


def test_upload_rejects_missing_schedule_time(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")
    with pytest.raises(ValueError, match="requires publish_at"):
        youtube_uploader.upload_video(
            FakeYouTube(response={"id": "x"}),
            lesson(),
            metadata(),
            video,
            mode="scheduled",
        )


def test_upload_rejects_non_future_schedule(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")
    with pytest.raises(ValueError, match="future"):
        youtube_uploader.upload_video(
            FakeYouTube(response={"id": "x"}),
            lesson(),
            metadata(),
            video,
            mode="scheduled",
            publish_at=datetime(2026, 10, 7, 11, tzinfo=timezone.utc),
            now=datetime(2026, 10, 7, 12, tzinfo=timezone.utc),
        )


def test_upload_fails_closed_on_api_error(monkeypatch, tmp_path):
    patch_media(monkeypatch)
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")

    with pytest.raises(RuntimeError, match="upload failed"):
        youtube_uploader.upload_video(
            FakeYouTube(error=RuntimeError("network")),
            lesson(),
            metadata(),
            video,
            mode="public",
        )


def test_upload_rejects_response_without_video_id(monkeypatch, tmp_path):
    patch_media(monkeypatch)
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")

    with pytest.raises(RuntimeError, match="no video ID"):
        youtube_uploader.upload_video(
            FakeYouTube(response={}),
            lesson(),
            metadata(),
            video,
            mode="public",
        )


def test_upload_rejects_missing_video(tmp_path):
    with pytest.raises(RuntimeError, match="does not exist"):
        youtube_uploader.upload_video(
            FakeYouTube(response={"id": "x"}),
            lesson(),
            metadata(),
            tmp_path / "missing.mp4",
            mode="public",
        )


def test_upload_rejects_final_description_over_api_limit(monkeypatch, tmp_path):
    patch_media(monkeypatch)
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")
    oversized = metadata()
    oversized = VideoMetadata(
        primary_title=oversized.primary_title,
        title_candidates=oversized.title_candidates,
        description="अ" * 4999,
        hashtags=oversized.hashtags,
        tags=oversized.tags,
        series_context=oversized.series_context,
    )

    with pytest.raises(RuntimeError, match="final YouTube description exceeds"):
        youtube_uploader.upload_video(
            FakeYouTube(response={"id": "x"}),
            lesson(),
            oversized,
            video,
            mode="public",
        )


def test_upload_shorts_records_shorts_content_format(monkeypatch, tmp_path):
    patch_media(monkeypatch)
    video = tmp_path / "short.mp4"
    video.write_bytes(b"video")
    history = tmp_path / "history.json"
    youtube = FakeYouTube(response={"id": "short123"})

    result = youtube_uploader.upload_video(
        youtube,
        lesson(),
        metadata(),
        video,
        mode="public",
        history_path=history,
        content_format="shorts",
        now=datetime(2026, 10, 7, 12, tzinfo=timezone.utc),
    )

    assert result == "short123"
    assert '"content_format": "shorts"' in history.read_text(encoding="utf-8")


def test_upload_rejects_invalid_content_format(monkeypatch, tmp_path):
    patch_media(monkeypatch)
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")

    with pytest.raises(ValueError, match="content_format"):
        youtube_uploader.upload_video(
            FakeYouTube(response={"id": "x"}),
            lesson(),
            metadata(),
            video,
            mode="public",
            content_format="vertical",
        )
