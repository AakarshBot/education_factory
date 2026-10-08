from __future__ import annotations

import argparse

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any

from channel_history import HistoryEntry, load_history, save_history
from youtube_auth import get_youtube_analytics_client, get_youtube_client

METRICS = (
    "views,engagedViews,estimatedMinutesWatched,averageViewDuration,"
    "averageViewPercentage,likes,comments,subscribersGained"
)
MAX_VIDEO_IDS_PER_REQUEST = 500


def _validate_dates(start_date: date, end_date: date) -> None:
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        raise TypeError("start_date and end_date must be dates")
    if start_date > end_date:
        raise ValueError("start_date must not be after end_date")


def _default_window(days: int) -> tuple[date, date]:
    if days < 1:
        raise ValueError("days must be at least 1")
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=days - 1)
    return start_date, end_date


def _parse_report(body: dict[str, Any]) -> dict[str, dict[str, float]]:
    headers = body.get("columnHeaders")
    rows = body.get("rows", [])
    if not isinstance(headers, list) or not isinstance(rows, list):
        raise RuntimeError("YouTube Analytics returned an invalid report")

    names = [header.get("name") for header in headers if isinstance(header, dict)]
    if not names or names[0] != "video":
        raise RuntimeError("YouTube Analytics report is missing the video dimension")

    metrics: dict[str, dict[str, float]] = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != len(names):
            raise RuntimeError("YouTube Analytics returned an invalid report row")
        video_id = row[0]
        if not isinstance(video_id, str) or not video_id:
            raise RuntimeError("YouTube Analytics returned an invalid video ID")

        values: dict[str, float] = {}
        for name, value in zip(names[1:], row[1:]):
            try:
                values[name] = float(value)
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    f"YouTube Analytics returned a non-numeric value for {name}"
                ) from exc
        metrics[video_id] = values

    return metrics


def fetch_video_metrics(
    youtube_analytics,
    video_ids: list[str] | tuple[str, ...],
    *,
    start_date: date,
    end_date: date,
) -> dict[str, dict[str, float]]:
    _validate_dates(start_date, end_date)

    cleaned_ids = []
    for video_id in video_ids:
        if not isinstance(video_id, str) or not video_id.strip():
            raise ValueError("video_ids must contain non-empty strings")
        cleaned_ids.append(video_id.strip())

    if len(set(cleaned_ids)) != len(cleaned_ids):
        raise ValueError("video_ids must be unique")
    if not cleaned_ids:
        return {}

    metrics: dict[str, dict[str, float]] = {}
    for offset in range(0, len(cleaned_ids), MAX_VIDEO_IDS_PER_REQUEST):
        batch = cleaned_ids[offset : offset + MAX_VIDEO_IDS_PER_REQUEST]
        try:
            body = (
                youtube_analytics.reports()
                .query(
                    ids="channel==MINE",
                    startDate=start_date.isoformat(),
                    endDate=end_date.isoformat(),
                    metrics=METRICS,
                    dimensions="video",
                    filters="video==" + ",".join(batch),
                )
                .execute()
            )
        except Exception as exc:
            raise RuntimeError("YouTube Analytics metrics query failed") from exc

        parsed = _parse_report(body)
        for video_id, values in parsed.items():
            metrics[video_id] = values

    return metrics



def fetch_recent_channel_videos(youtube, limit: int) -> list[dict[str, Any]]:
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")

    try:
        channels = youtube.channels().list(part="contentDetails", mine=True).execute().get("items", [])
        if not channels or not isinstance(channels[0], dict):
            raise RuntimeError("YouTube returned no authenticated channel")
        uploads_id = ((channels[0].get("contentDetails") or {}).get("relatedPlaylists") or {}).get("uploads")
        if not uploads_id:
            raise RuntimeError("YouTube channel has no uploads playlist")

        playlist = youtube.playlistItems().list(
            part="contentDetails,snippet",
            playlistId=uploads_id,
            maxResults=limit,
        ).execute()
        items = playlist.get("items", [])
        if not isinstance(items, list):
            raise RuntimeError("YouTube returned an invalid uploads playlist")
        ids = [
            str(item.get("contentDetails", {}).get("videoId"))
            for item in items
            if isinstance(item, dict) and item.get("contentDetails", {}).get("videoId")
        ]
        return [*fetch_video_statistics(youtube, ids).values()] if ids else []
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("YouTube channel upload lookup failed") from exc


def fetch_video_statistics(youtube, video_ids: list[str] | tuple[str, ...]) -> dict[str, dict[str, Any]]:
    if len(video_ids) > 50:
        raise ValueError("video_ids must contain 50 or fewer IDs")
    ids = [video_id.strip() for video_id in video_ids]
    if any(not video_id for video_id in ids):
        raise ValueError("video_ids must contain non-empty strings")
    if len(set(ids)) != len(ids):
        raise ValueError("video_ids must be unique")
    if not ids:
        return {}

    try:
        items = youtube.videos().list(
            part="snippet,statistics,status",
            id=",".join(ids),
        ).execute().get("items", [])
    except Exception as exc:
        raise RuntimeError("YouTube video statistics query failed") from exc

    if not isinstance(items, list):
        raise RuntimeError("YouTube Data API returned an invalid video list")

    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            raise RuntimeError("YouTube Data API returned an invalid video")
        stats = item.get("statistics") or {}
        snippet = item.get("snippet") or {}
        status = item.get("status") or {}
        result[str(item["id"])] = {
            "title": str(snippet.get("title", "")),
            "publishedAt": snippet.get("publishedAt"),
            "views": int(stats["viewCount"]) if "viewCount" in stats else None,
            "likes": int(stats["likeCount"]) if "likeCount" in stats else None,
            "comments": int(stats["commentCount"]) if "commentCount" in stats else None,
            "privacyStatus": status.get("privacyStatus"),
            "publishAt": status.get("publishAt"),
        }
    return result


def _published_at(entry: HistoryEntry, current: dict[str, Any]) -> datetime | None:
    value = current.get("publishedAt") or entry.published_at
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _snapshot(
    history_path: str | Path,
    *,
    limit: int,
    days: int,
    youtube,
    youtube_analytics,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], date, list[str]]:
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")
    if days < 1:
        raise ValueError("days must be at least 1")

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None or current_time.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    entries = [entry for entry in load_history(Path(history_path)) if entry.video_id]
    history_by_id = {str(entry.video_id): entry for entry in entries}
    uploaded = fetch_recent_channel_videos(youtube, limit)
    uploaded_by_id = {item["video_id"]: item for item in uploaded}
    missing_history = [video_id for video_id in history_by_id if video_id not in uploaded_by_id]

    ordered_ids = [item["video_id"] for item in uploaded]
    published = []
    for video_id in ordered_ids:
        entry = history_by_id.get(video_id, HistoryEntry(
            exam="", subject="", topic="", lesson_type="", title=uploaded_by_id[video_id].get("title", ""),
            status="", created_at="", video_id=video_id,
        ))
        published.append(_published_at(entry, uploaded_by_id[video_id]))
    published_dates = [value.date() for value in published if value is not None]
    end_date = current_time.astimezone(ZoneInfo("America/Los_Angeles")).date() - timedelta(days=1)

    analytics: dict[str, dict[str, float]] = {}
    if published_dates and min(published_dates) <= end_date:
        start_date = max(end_date - timedelta(days=days - 1), min(published_dates))
        analytics = fetch_video_metrics(
            youtube_analytics,
            ordered_ids,
            start_date=start_date,
            end_date=end_date,
        )

    result = []
    for video_id, publication in zip(ordered_ids, published):
        video = uploaded_by_id[video_id]
        metrics = analytics.get(video_id, {})
        entry = history_by_id.get(video_id)
        age_hours = (
            max(0.0, (current_time - publication).total_seconds() / 3600)
            if publication
            else None
        )
        views = video.get("views")
        result.append(
            {
                "content_format": entry.content_format if entry else "unknown",
                "title": video.get("title") or (entry.title if entry else video_id),
                "video_id": video_id,
                "published_at": publication,
                "age_hours": age_hours,
                "views": views,
                "views_per_hour": views / age_hours if views is not None and age_hours and age_hours >= 1 else None,
                "engaged_views": metrics.get("engagedViews"),
                "watch_minutes": metrics.get("estimatedMinutesWatched"),
                "average_view_duration": metrics.get("averageViewDuration"),
                "average_view_percentage": metrics.get("averageViewPercentage"),
                "subscribers_gained": metrics.get("subscribersGained"),
                "likes": video.get("likes"),
                "comments": video.get("comments"),
                "privacy_status": video.get("privacyStatus"),
                "publish_at": video.get("publishAt"),
            }
        )

    return result[:limit], end_date, missing_history[:limit]



def _snapshot_value(value: float | int | None) -> str:
    return "—" if value is None else f"{value:,.0f}"


def _snapshot_percent(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f}%"


def _snapshot_duration(value: float | None) -> str:
    if value is None:
        return "—"
    seconds = max(0, int(round(value)))
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"


def print_snapshot(*, history_path: str | Path = "data/channel_history.json", limit: int = 10, days: int = 30) -> None:
    entries = load_history(Path(history_path))
    if not any(entry.video_id for entry in entries):
        print(f"No YouTube video IDs found in {history_path}.")
        return

    snapshot, analytics_through, missing_history = _snapshot(
        history_path,
        limit=limit,
        days=days,
        youtube=get_youtube_client(),
        youtube_analytics=get_youtube_analytics_client(),
    )
    print("Education Factory — YouTube analytics snapshot")
    print(f"Analytics requested through: {analytics_through.isoformat()}")
    print("Current counters: views/likes/comments | Analytics: engaged views/watch time/average view metrics/subscribers")
    if missing_history:
        print("History IDs not present in the channel uploads list:")
        for video_id in missing_history:
            print(f"  {video_id}")
        print()

    for content_format, label in (("long_form", "Long-form"), ("shorts", "Shorts")):
        videos = [item for item in snapshot if item["content_format"] == content_format]
        print(label)
        if not videos:
            print("  No videos found.")
            print()
            continue
        for item in videos:
            published = item["published_at"].isoformat(timespec="minutes") if item["published_at"] else "unknown"
            age = f"{item['age_hours']:.1f}h" if item["age_hours"] is not None else "unknown"
            rate = f"{item['views_per_hour']:.1f}" if item["views_per_hour"] is not None else "—"
            print(f"  {item['title']}")
            schedule = item["publish_at"] or "—"
            print(f"    Published: {published} UTC | Age: {age} | Visibility: {item['privacy_status'] or 'not returned'}")
            if schedule != "—":
                print(f"    Scheduled publishAt: {schedule}")
            print(f"    Views: {_snapshot_value(item['views'])} | Views/hour: {rate}")
            print(f"    Engaged views: {_snapshot_value(item['engaged_views'])} | Watch: {_snapshot_value(item['watch_minutes'])} min | Avg view: {_snapshot_duration(item['average_view_duration'])} | Avg %: {_snapshot_percent(item['average_view_percentage'])}")
            print(f"    Subscribers gained: {_snapshot_value(item['subscribers_gained'])} | Likes: {_snapshot_value(item['likes'])} | Comments: {_snapshot_value(item['comments'])}")
            print(f"    Video ID: {item['video_id']}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a read-only snapshot of recent YouTube performance.")
    parser.add_argument("--history-path", default="data/channel_history.json")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()
    print_snapshot(history_path=args.history_path, limit=args.limit, days=args.days)


if __name__ == "__main__":
    main()

def ingest_metrics(
    *,
    history_path: str | Path = "data/channel_history.json",
    start_date: date | None = None,
    end_date: date | None = None,
    days: int = 30,
    youtube_analytics=None,
) -> list[HistoryEntry]:
    if (start_date is None) != (end_date is None):
        raise ValueError("start_date and end_date must be provided together")

    if start_date is None:
        start_date, end_date = _default_window(days)

    assert end_date is not None
    _validate_dates(start_date, end_date)

    path = Path(history_path)
    entries = load_history(path)
    video_ids = [entry.video_id for entry in entries if entry.video_id]
    if not video_ids:
        return entries

    if youtube_analytics is None:
        youtube_analytics = get_youtube_analytics_client()

    metrics_by_video = fetch_video_metrics(
        youtube_analytics,
        video_ids,
        start_date=start_date,
        end_date=end_date,
    )

    updated = [
        replace(entry, metrics=metrics_by_video.get(entry.video_id or "", entry.metrics))
        for entry in entries
    ]
    if updated != entries:
        save_history(updated, path)
    return updated
