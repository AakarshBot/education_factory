from __future__ import annotations

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



def fetch_video_statistics(
    youtube,
    video_ids: list[str] | tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    if len(video_ids) > 50:
        raise ValueError("video_ids must contain 50 or fewer IDs")

    cleaned_ids = []
    for video_id in video_ids:
        if not isinstance(video_id, str) or not video_id.strip():
            raise ValueError("video_ids must contain non-empty strings")
        cleaned_ids.append(video_id.strip())

    if len(set(cleaned_ids)) != len(cleaned_ids):
        raise ValueError("video_ids must be unique")
    if not cleaned_ids:
        return {}

    try:
        body = (
            youtube.videos()
            .list(
                part="snippet,statistics,status",
                id=",".join(cleaned_ids),
            )
            .execute()
        )
    except Exception as exc:
        raise RuntimeError("YouTube video statistics query failed") from exc

    items = body.get("items", [])
    if not isinstance(items, list):
        raise RuntimeError("YouTube Data API returned an invalid video list")

    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            raise RuntimeError("YouTube Data API returned an invalid video")
        video_id = str(item["id"])
        snippet = item.get("snippet") or {}
        statistics = item.get("statistics") or {}
        status = item.get("status") or {}

        current: dict[str, Any] = {
            "title": str(snippet.get("title", "")),
            "publishedAt": snippet.get("publishedAt"),
            "privacyStatus": status.get("privacyStatus"),
        }
        for key, output_key in (
            ("viewCount", "views"),
            ("likeCount", "likes"),
            ("commentCount", "comments"),
        ):
            if key in statistics:
                try:
                    current[output_key] = int(statistics[key])
                except (TypeError, ValueError) as exc:
                    raise RuntimeError(
                        f"YouTube Data API returned invalid {key} for {video_id}"
                    ) from exc

        result[video_id] = current

    return result


def _published_at(
    entry: HistoryEntry,
    statistics: dict[str, Any],
) -> datetime | None:
    value = statistics.get("publishedAt") or entry.published_at
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_age(hours: float) -> str:
    total_minutes = max(0, int(hours * 60))
    days, remainder = divmod(total_minutes, 1440)
    hours, minutes = divmod(remainder, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    total_seconds = max(0, int(round(seconds)))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def _format_number(value: float | int | None) -> str:
    if value is None:
        return "—"
    return f"{int(value):,}"


def _format_percent(value: float | None) -> str:
    return f"{value:.1f}%" if value is not None else "—"


def _latest_complete_analytics_date(now: datetime) -> date:
    return now.astimezone(ZoneInfo("America/Los_Angeles")).date() - timedelta(days=1)


def _snapshot_entries(
    history_path: str | Path,
    *,
    limit: int,
    days: int,
    youtube,
    youtube_analytics,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], date]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if limit > 50:
        raise ValueError("limit must be 50 or fewer")
    if days < 1:
        raise ValueError("days must be at least 1")

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    entries = [entry for entry in load_history(Path(history_path)) if entry.video_id]
    if not entries:
        return [], _latest_complete_analytics_date(current)

    entries = entries[-limit:]
    video_ids = [str(entry.video_id) for entry in entries]
    statistics_by_video = fetch_video_statistics(youtube, video_ids)

    published_dates = [
        _published_at(entry, statistics_by_video.get(str(entry.video_id), {}))
        for entry in entries
    ]
    published_dates = [value for value in published_dates if value is not None]
    end_date = _latest_complete_analytics_date(current)

    if published_dates and min(published_dates).date() <= end_date:
        start_date = max(
            end_date - timedelta(days=days - 1),
            min(value.date() for value in published_dates),
        )
        analytics_by_video = fetch_video_metrics(
            youtube_analytics,
            video_ids,
            start_date=start_date,
            end_date=end_date,
        )
    else:
        analytics_by_video = {}

    snapshot: list[dict[str, Any]] = []
    for entry in entries:
        video_id = str(entry.video_id)
        statistics = statistics_by_video.get(video_id, {})
        metrics = analytics_by_video.get(video_id, {})
        published = _published_at(entry, statistics)
        age_hours = (
            max(0.0, (current - published).total_seconds() / 3600)
            if published
            else None
        )
        views = statistics.get("views")

        snapshot.append(
            {
                "content_format": entry.content_format,
                "title": statistics.get("title") or entry.title,
                "video_id": video_id,
                "published_at": published,
                "age_hours": age_hours,
                "views": views,
                "views_per_hour": (
                    views / age_hours
                    if views is not None and age_hours is not None and age_hours >= 1
                    else None
                ),
                "engaged_views": metrics.get("engagedViews"),
                "estimated_minutes_watched": metrics.get("estimatedMinutesWatched"),
                "average_view_duration": metrics.get("averageViewDuration"),
                "average_view_percentage": metrics.get("averageViewPercentage"),
                "subscribers_gained": metrics.get("subscribersGained"),
                "likes": statistics.get("likes"),
                "comments": statistics.get("comments"),
                "privacy_status": statistics.get("privacyStatus"),
            }
        )

    snapshot.sort(
        key=lambda item: item["published_at"]
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return snapshot[:limit], end_date


def print_snapshot(
    *,
    history_path: str | Path = "data/channel_history.json",
    limit: int = 10,
    days: int = 30,
) -> None:
    entries = load_history(Path(history_path))
    if not any(entry.video_id for entry in entries):
        print(f"No YouTube video IDs found in {history_path}.")
        return

    youtube = get_youtube_client()
    youtube_analytics = get_youtube_analytics_client()
    snapshot, analytics_through = _snapshot_entries(
        history_path,
        limit=limit,
        days=days,
        youtube=youtube,
        youtube_analytics=youtube_analytics,
    )

    now = datetime.now(timezone.utc)
    print("Education Factory — YouTube analytics snapshot")
    print(f"Run time: {now.astimezone().isoformat(timespec='minutes')}")
    print(f"Analytics requested through: {analytics_through.isoformat()}")
    print("Current counters: YouTube Data API views/likes/comments")
    print("Analytics: engaged views/watch time/average view metrics/subscribers gained")
    print()

    for content_format in ("long_form", "shorts"):
        videos = [item for item in snapshot if item["content_format"] == content_format]
        label = "Long-form" if content_format == "long_form" else "Shorts"
        print(label)
        if not videos:
            print("  No videos found.")
            print()
            continue

        for item in videos:
            published = item["published_at"]
            published_label = (
                published.isoformat(timespec="minutes") if published else "unknown"
            )
            age_label = (
                _format_age(item["age_hours"])
                if item["age_hours"] is not None
                else "unknown"
            )
            views_per_hour = (
                f"{item['views_per_hour']:.1f}"
                if item["views_per_hour"] is not None
                else "—"
            )
            print(f"  {item['title']}")
            print(
                f"    Published: {published_label} UTC | Age: {age_label} | "
                f"Status: {item['privacy_status'] or 'unknown'}"
            )
            print(
                f"    Views: {_format_number(item['views'])} | "
                f"Views/hour: {views_per_hour} | "
                f"Engaged views: {_format_number(item['engaged_views'])}"
            )
            print(
                f"    Watch time: {_format_number(item['estimated_minutes_watched'])} min | "
                f"Avg view: {_format_duration(item['average_view_duration'])} | "
                f"Avg % viewed: {_format_percent(item['average_view_percentage'])}"
            )
            print(
                f"    Subscribers gained: {_format_number(item['subscribers_gained'])} | "
                f"Likes: {_format_number(item['likes'])} | "
                f"Comments: {_format_number(item['comments'])}"
            )
            print(f"    Video ID: {item['video_id']}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print a read-only snapshot of recent YouTube performance."
    )
    parser.add_argument("--history-path", default="data/channel_history.json")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()
    print_snapshot(
        history_path=args.history_path,
        limit=args.limit,
        days=args.days,
    )


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
