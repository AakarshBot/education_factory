from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

import requests

from config import YOUTUBE_API_KEY, validate_config

_YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

EXAMS = ("SSC", "Banking", "Railway")
SUBJECTS = ("Maths", "Reasoning", "English")
DEFAULT_DEMAND_QUERIES = tuple(
    f"{exam} {subject} 2026"
    for exam in EXAMS
    for subject in SUBJECTS
)


@dataclass(frozen=True)
class DemandSignal:
    query: str
    order: str
    video_id: str
    title: str
    channel_title: str
    published_at: str
    description: str
    rank: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "order": self.order,
            "video_id": self.video_id,
            "title": self.title,
            "channel_title": self.channel_title,
            "published_at": self.published_at,
            "description": self.description,
            "rank": self.rank,
        }


def _published_after(days: int) -> str:
    if days < 1:
        raise ValueError("days must be at least 1")
    return (
        datetime.now(timezone.utc) - timedelta(days=days)
    ).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _search(
    query: str,
    *,
    order: str,
    published_after: str,
    max_results: int,
    region_code: str,
) -> list[DemandSignal]:
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": order,
        "publishedAfter": published_after,
        "maxResults": max_results,
        "regionCode": region_code,
        "relevanceLanguage": "en",
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(_YOUTUBE_SEARCH_URL, params=params, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(
            f"YouTube demand discovery failed ({response.status_code}): "
            f"{response.text[:500]}"
        )

    try:
        items = response.json()["items"]
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("YouTube returned an invalid demand response") from exc

    signals: list[DemandSignal] = []
    for rank, item in enumerate(items, start=1):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id or not isinstance(snippet, dict):
            continue

        signals.append(
            DemandSignal(
                query=query,
                order=order,
                video_id=video_id,
                title=str(snippet.get("title", "")).strip(),
                channel_title=str(snippet.get("channelTitle", "")).strip(),
                published_at=str(snippet.get("publishedAt", "")).strip(),
                description=str(snippet.get("description", "")).strip(),
                rank=rank,
            )
        )

    return signals


def discover_demand(
    queries: Sequence[str] = DEFAULT_DEMAND_QUERIES,
    *,
    days: int = 30,
    max_results: int = 10,
    region_code: str = "IN",
) -> list[DemandSignal]:
    if not queries:
        raise ValueError("queries must not be empty")
    if max_results < 1 or max_results > 50:
        raise ValueError("max_results must be between 1 and 50")
    if days < 1:
        raise ValueError("days must be at least 1")

    clean_queries = tuple(query.strip() for query in queries)
    if any(not query for query in clean_queries):
        raise ValueError("queries must not contain empty values")

    validate_config(require_youtube_api=True)

    published_after = _published_after(days)
    signals: list[DemandSignal] = []

    for query in clean_queries:
        signals.extend(
            _search(
                query,
                order="relevance",
                published_after=published_after,
                max_results=max_results,
                region_code=region_code,
            )
        )
        signals.extend(
            _search(
                query,
                order="viewCount",
                published_after=published_after,
                max_results=max_results,
                region_code=region_code,
            )
        )

    return signals
