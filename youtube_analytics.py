from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from channel_history import HistoryEntry, load_history, save_history
from youtube_auth import get_youtube_analytics_client

METRICS = (
    "views,estimatedMinutesWatched,averageViewDuration,"
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
