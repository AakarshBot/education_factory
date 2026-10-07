from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from googleapiclient.http import MediaFileUpload

from channel_history import DEFAULT_HISTORY_FILE, HistoryEntry, append_history
from lesson import Lesson
from metadata_generator import VideoMetadata

ALLOWED_MODES = frozenset({"public", "scheduled"})
ALLOWED_CONTENT_FORMATS = frozenset({"long_form", "shorts"})


def _youtube_description(metadata: VideoMetadata) -> str:
    description = metadata.description
    if metadata.hashtags:
        description = f"{description}\n\n{' '.join(metadata.hashtags)}"
    if len(description.encode("utf-8")) > 5000:
        raise RuntimeError("final YouTube description exceeds 5000 UTF-8 bytes")
    return description


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _scheduled_iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("publish_at must be timezone-aware")
    scheduled = value.astimezone(timezone.utc)
    if scheduled <= datetime.now(timezone.utc):
        raise ValueError("publish_at must be in the future")
    return scheduled.isoformat().replace("+00:00", "Z")


def upload_video(
    youtube,
    lesson: Lesson,
    metadata: VideoMetadata,
    video_path: str | Path,
    *,
    mode: str = "scheduled",
    publish_at: datetime | None = None,
    history_path: str | Path = DEFAULT_HISTORY_FILE,
    now: datetime | None = None,
    content_format: str = "long_form",
    english_metadata: VideoMetadata | None = None,
) -> str:
    if not isinstance(lesson, Lesson):
        raise TypeError("lesson must be a Lesson")
    if not isinstance(metadata, VideoMetadata):
        raise TypeError("metadata must be VideoMetadata")
    if english_metadata is not None and not isinstance(english_metadata, VideoMetadata):
        raise TypeError("english_metadata must be VideoMetadata or None")

    selected_mode = mode.strip().lower()
    if selected_mode not in ALLOWED_MODES:
        raise ValueError("mode must be 'public' or 'scheduled'")
    selected_format = content_format.strip().lower()
    if selected_format not in ALLOWED_CONTENT_FORMATS:
        raise ValueError("content_format must be 'long_form' or 'shorts'")

    video = Path(video_path).expanduser()
    if not video.exists() or not video.is_file() or video.stat().st_size == 0:
        raise RuntimeError(f"video file does not exist or is empty: {video}")

    if selected_mode == "public" and publish_at is not None:
        raise ValueError("publish_at is only valid for scheduled mode")
    if selected_mode == "scheduled" and publish_at is None:
        raise ValueError("scheduled mode requires publish_at")

    current_time = now or datetime.now(timezone.utc)
    created_at = _utc_iso(current_time)
    scheduled_at = _scheduled_iso(publish_at) if publish_at is not None else None

    description = _youtube_description(metadata)
    body = {
        "snippet": {
            "title": metadata.primary_title,
            "description": description,
            "tags": list(metadata.tags),
            "categoryId": metadata.category_id,
            "defaultLanguage": metadata.default_language,
            "defaultAudioLanguage": "hi",
        },
        "status": {
            "privacyStatus": "private" if scheduled_at else "public",
        },
    }
    if scheduled_at:
        body["status"]["publishAt"] = scheduled_at
    if english_metadata is not None:
        body["localizations"] = {
            "en": {
                "title": english_metadata.primary_title,
                "description": _youtube_description(english_metadata),
            }
        }

    try:
        request = youtube.videos().insert(
            part="snippet,status" + (",localizations" if english_metadata is not None else ""),
            body=body,
            media_body=MediaFileUpload(
                str(video),
                mimetype="video/mp4",
                chunksize=-1,
                resumable=True,
            ),
        )
        response = None
        while response is None:
            _, response = request.next_chunk()
    except Exception as exc:
        raise RuntimeError("YouTube video upload failed") from exc

    if not isinstance(response, dict) or not response.get("id"):
        raise RuntimeError("YouTube upload returned no video ID")

    status = "scheduled" if scheduled_at else "published"
    published_at = scheduled_at or created_at
    entry = HistoryEntry(
        exam=lesson.exam,
        subject=lesson.subject,
        topic=lesson.topic,
        lesson_type=lesson.lesson_type,
        title=metadata.primary_title,
        status=status,
        created_at=created_at,
        video_id=str(response["id"]),
        published_at=published_at,
        metrics={},
        content_format=selected_format,
    )

    try:
        append_history(entry, Path(history_path))
    except Exception as exc:
        raise RuntimeError(
            f"YouTube video {response['id']} uploaded but channel history could not be updated"
        ) from exc

    return str(response["id"])
