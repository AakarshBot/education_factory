from __future__ import annotations

import json
import time
import re
from dataclasses import dataclass
from typing import Any

import requests

from config import GEMINI_API_KEY, GEMINI_MODEL, validate_config
from lesson import Lesson

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
EDUCATION_CATEGORY_ID = "27"

_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title_candidates": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 5,
            "maxItems": 5,
        },
        "description": {"type": "string"},
        "hashtags": {
            "type": "array",
            "items": {"type": "string"},
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
        },
        "series_context": {"type": "string"},
    },
    "required": [
        "title_candidates",
        "description",
        "hashtags",
        "tags",
        "series_context",
    ],
}


@dataclass(frozen=True)
class VideoMetadata:
    primary_title: str
    title_candidates: tuple[str, ...]
    description: str
    hashtags: tuple[str, ...]
    tags: tuple[str, ...]
    series_context: str
    category_id: str = EDUCATION_CATEGORY_ID
    default_language: str = "hi"

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_title": self.primary_title,
            "title_candidates": list(self.title_candidates),
            "description": self.description,
            "hashtags": list(self.hashtags),
            "tags": list(self.tags),
            "series_context": self.series_context,
            "category_id": self.category_id,
            "default_language": self.default_language,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VideoMetadata":
        return cls(
            primary_title=data["primary_title"],
            title_candidates=tuple(data["title_candidates"]),
            description=data["description"],
            hashtags=tuple(data["hashtags"]),
            tags=tuple(data["tags"]),
            series_context=data["series_context"],
            category_id=data.get("category_id", EDUCATION_CATEGORY_ID),
            default_language=data.get("default_language", "hi"),
        )


def _request_metadata(lesson: Lesson, language: str) -> dict[str, Any]:
    source_references = sorted(
        {
            question.source_reference.strip()
            for question in lesson.questions
            if question.source_reference and question.source_reference.strip()
        }
    )
    facts = {
        "lesson_title": lesson.title,
        "lesson_type": lesson.lesson_type,
        "exam": lesson.exam,
        "subject": lesson.subject,
        "topic": lesson.topic,
        "question_count": len(lesson.questions),
        "segment_kinds": [segment.kind for segment in lesson.segments],
        "source_references": source_references,
    }

    prompt = f"""
Create YouTube metadata for one educational video.

Output language: {language}

Use ONLY these supplied facts:
{json.dumps(facts, ensure_ascii=False)}

Return exactly 5 distinct title candidates. The first title must be the strongest overall choice.
Titles should be concise, specific, useful to the intended Indian competitive-exam audience, and normally around 45-65 characters when practical. They must describe what the video actually teaches or practices.
Do not use fake urgency, guaranteed results, "100% sure", exaggerated claims, or unrelated trending terms.

Write one unique description that explains what the viewer will practice or learn and naturally includes the exam, subject, and topic. Keep it useful rather than keyword-stuffed.
Mention source information only when source_references are supplied.
Do not invent chapters, dates, scores, difficulty claims, downloadable material, links, instructors, certifications, or outcomes.

Return 3-5 directly relevant hashtags. Every hashtag must be directly related to the supplied lesson facts.
Return a small set of relevant keyword tags. Tags are secondary metadata, so prefer a few precise phrases over repetition.
Return a short series_context label that describes the recurring learning format, such as "SSC Maths Practice" or "Banking Reasoning Timed Test".

Do not include angle brackets in any field.
Do not include URLs.
""".strip()

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        "You write trustworthy YouTube metadata for an Indian education channel. "
                        "Never manufacture facts or promises. Optimize for clarity and viewer intent, "
                        "not keyword stuffing."
                    )
                }
            ]
        },
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": _RESPONSE_SCHEMA,
        },
    }

    response = None
    for attempt, delay in enumerate((0, 1, 2, 4)):
        if delay:
            time.sleep(delay)
        response = requests.post(
            _GEMINI_URL.format(model=GEMINI_MODEL),
            headers={
                "x-goog-api-key": GEMINI_API_KEY,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        if response.status_code not in {429, 503} or attempt == 3:
            break

    assert response is not None
    if response.status_code != 200:
        raise RuntimeError(
            f"Gemini metadata generation failed ({response.status_code}): "
            f"{response.text[:500]}"
        )

    try:
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Gemini returned an invalid structured metadata response") from exc

    return data


def _clean_values(values: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(values, list) or not values:
        raise RuntimeError(f"metadata field '{field}' must be a non-empty list")
    cleaned = tuple(value.strip() for value in values if isinstance(value, str) and value.strip())
    if len(cleaned) != len(values):
        raise RuntimeError(f"metadata field '{field}' contains invalid values")
    if len(set(value.casefold() for value in cleaned)) != len(cleaned):
        raise RuntimeError(f"metadata field '{field}' contains duplicates")
    if any("<" in value or ">" in value for value in cleaned):
        raise RuntimeError(f"metadata field '{field}' contains invalid characters")
    return cleaned


def generate_metadata(lesson: Lesson, *, language: str = "Hinglish") -> VideoMetadata:
    if not isinstance(lesson, Lesson):
        raise TypeError("lesson must be a Lesson")
    if not language.strip():
        raise ValueError("language must not be empty")

    validate_config(require_gemini=True)
    data = _request_metadata(lesson, language.strip())

    titles = _clean_values(data.get("title_candidates"), field="title_candidates")
    if len(titles) != 5:
        raise RuntimeError("metadata must contain exactly 5 title candidates")
    if any(len(title) > 100 for title in titles):
        raise RuntimeError("metadata title exceeds 100 characters")
    if any(re.search(r"\s{3,}", title) for title in titles):
        raise RuntimeError("metadata title contains excessive spacing")

    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        raise RuntimeError("metadata description must not be empty")
    description = description.strip()
    if "<" in description or ">" in description:
        raise RuntimeError("metadata description contains invalid characters")
    if len(description.encode("utf-8")) > 5000:
        raise RuntimeError("metadata description exceeds 5000 UTF-8 bytes")
    if "http://" in description.lower() or "https://" in description.lower():
        raise RuntimeError("metadata description must not contain URLs")

    hashtags = _clean_values(data.get("hashtags"), field="hashtags")
    if not 3 <= len(hashtags) <= 5:
        raise RuntimeError("metadata must contain 3 to 5 hashtags")
    if any(not tag.startswith("#") or len(tag) == 1 for tag in hashtags):
        raise RuntimeError("hashtags must start with #")
    if any(" " in tag for tag in hashtags):
        raise RuntimeError("hashtags must not contain spaces")
    if any(not tag[1:].replace("_", "").isalnum() for tag in hashtags):
        raise RuntimeError("hashtags contain invalid characters")

    tags = _clean_values(data.get("tags"), field="tags")
    tag_length = sum(len(tag) for tag in tags) + max(0, len(tags) - 1)
    if tag_length > 500:
        raise RuntimeError("metadata tags exceed 500 characters")

    series_context = data.get("series_context")
    if not isinstance(series_context, str) or not series_context.strip():
        raise RuntimeError("metadata series_context must not be empty")
    series_context = series_context.strip()

    return VideoMetadata(
        primary_title=titles[0],
        title_candidates=titles,
        description=description,
        hashtags=hashtags,
        tags=tags,
        series_context=series_context,
    )
