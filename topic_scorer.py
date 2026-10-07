from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Sequence

import requests

from config import GEMINI_API_KEY, GEMINI_MODEL, validate_config
from demand_discovery import DemandSignal

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_TRANSIENT_STATUS_CODES = frozenset({429, 503})
_RETRY_DELAYS = (1, 2, 4)

_SCORE_WEIGHTS = {
    "demand": 0.25,
    "exam_relevance": 0.20,
    "novelty": 0.15,
    "educational_value": 0.20,
    "visual_potential": 0.10,
    "production_reliability": 0.10,
}

_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "exam": {"type": "string"},
                    "subject": {"type": "string"},
                    "topic": {"type": "string"},
                    "signal_indices": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                    "exam_relevance": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "novelty": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "educational_value": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "visual_potential": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "production_reliability": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "rationale": {"type": "string"},
                },
                "required": [
                    "exam",
                    "subject",
                    "topic",
                    "signal_indices",
                    "exam_relevance",
                    "novelty",
                    "educational_value",
                    "visual_potential",
                    "production_reliability",
                    "rationale",
                ],
            },
        }
    },
    "required": ["candidates"],
}


@dataclass(frozen=True)
class TopicScore:
    exam: str
    subject: str
    topic: str
    demand_score: float
    exam_relevance: int
    novelty: int
    educational_value: int
    visual_potential: int
    production_reliability: int
    total_score: float
    supporting_signal_indices: tuple[int, ...]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "exam": self.exam,
            "subject": self.subject,
            "topic": self.topic,
            "demand_score": self.demand_score,
            "exam_relevance": self.exam_relevance,
            "novelty": self.novelty,
            "educational_value": self.educational_value,
            "visual_potential": self.visual_potential,
            "production_reliability": self.production_reliability,
            "total_score": self.total_score,
            "supporting_signal_indices": self.supporting_signal_indices,
            "rationale": self.rationale,
        }


def _demand_scores(signals: Sequence[DemandSignal]) -> list[float]:
    max_rank = max(signal.rank for signal in signals)
    return [
        round(100 * (1 - (signal.rank - 1) / max_rank), 2)
        for signal in signals
    ]


def _request_candidates(
    signals: Sequence[DemandSignal],
    *,
    recent_titles: Sequence[str],
    language: str,
) -> list[dict[str, Any]]:
    indexed_signals = [
        {
            "index": index,
            "query": signal.query,
            "order": signal.order,
            "rank": signal.rank,
            "title": signal.title,
            "description": signal.description,
        }
        for index, signal in enumerate(signals)
    ]

    prompt = f"""
Identify concrete educational topic candidates for an Indian competitive-exam YouTube channel.

Locked exams: SSC, Banking, Railway.
Locked subjects: Maths, Reasoning, English.
Output language for rationale: {language}

Use only the supplied YouTube search signals. Group signals that point to the same underlying exam topic.
Do not invent demand data and do not assign a demand score; the application will calculate that from rank.
Do not return generic candidates such as "SSC Maths 2026".
Prefer specific teachable topics such as percentages, profit and loss, syllogism, coding-decoding, error spotting, etc.
Reject news/current-affairs topics and non-educational entertainment even if they appear in the search results.
Each candidate must cite at least one supporting signal index.

Score these five qualitative dimensions from 0 to 100:
- exam_relevance: direct usefulness for the named exam
- novelty: how distinct the topic is from the supplied recent channel titles
- educational_value: how much genuine teaching/practice value it can provide
- visual_potential: how naturally it supports clear instructional visuals
- production_reliability: how reliably the factory can create it with the current content engine

When the recent-title list is empty, there is no historical evidence; return a neutral novelty score of 50.
Do not use popularity or rankings to influence any qualitative score.

Recent channel titles:
{json.dumps(list(recent_titles), ensure_ascii=False)}

YouTube signals:
{json.dumps(indexed_signals, ensure_ascii=False)}
""".strip()

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        "You are the topic-analysis engine for an Indian competitive-exam "
                        "education channel. Be conservative: only identify topics supported "
                        "by the supplied signals and score semantic properties, not popularity."
                    )
                }
            ]
        },
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseFormat": {
                "text": {
                    "mimeType": "application/json",
                    "schema": _RESPONSE_SCHEMA,
                }
            },
        },
    }

    response = None
    for attempt in range(len(_RETRY_DELAYS) + 1):
        response = requests.post(
            _GEMINI_URL.format(model=GEMINI_MODEL),
            headers={
                "x-goog-api-key": GEMINI_API_KEY,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        if response.status_code not in _TRANSIENT_STATUS_CODES or attempt == len(_RETRY_DELAYS):
            break
        time.sleep(_RETRY_DELAYS[attempt])

    assert response is not None
    if response.status_code != 200:
        raise RuntimeError(
            f"Gemini topic scoring failed ({response.status_code}): "
            f"{response.text[:500]}"
        )

    try:
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        candidates = json.loads(text)["candidates"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Gemini returned an invalid structured topic response") from exc

    if not isinstance(candidates, list) or not candidates:
        raise RuntimeError("Gemini returned no topic candidates")

    return candidates


def score_topics(
    signals: Sequence[DemandSignal],
    *,
    recent_titles: Sequence[str] = (),
    language: str = "Hinglish",
) -> list[TopicScore]:
    if not signals:
        raise ValueError("signals must not be empty")
    if any(signal.rank < 1 for signal in signals):
        raise ValueError("signal ranks must be positive")

    clean_titles = tuple(title.strip() for title in recent_titles)
    if any(not title for title in clean_titles):
        raise ValueError("recent_titles must not contain empty values")

    validate_config(require_gemini=True)

    demand_scores = _demand_scores(signals)
    candidates = _request_candidates(
        signals,
        recent_titles=clean_titles,
        language=language,
    )

    results: list[TopicScore] = []
    seen: set[tuple[str, str, str]] = set()
    allowed_exams = {
        "ssc": "SSC",
        "banking": "Banking",
        "railway": "Railway",
    }
    allowed_subjects = {
        "maths": "Maths",
        "reasoning": "Reasoning",
        "english": "English",
    }

    for candidate in candidates:
        exam = candidate.get("exam")
        subject = candidate.get("subject")
        topic = candidate.get("topic")
        indices = candidate.get("signal_indices")

        if not isinstance(exam, str) or not exam.strip():
            raise RuntimeError("Topic candidate has invalid exam")
        if not isinstance(subject, str) or not subject.strip():
            raise RuntimeError("Topic candidate has invalid subject")
        if not isinstance(topic, str) or not topic.strip():
            raise RuntimeError("Topic candidate is empty")

        exam_key = exam.strip().lower()
        subject_key = subject.strip().lower()
        key = (exam_key, subject_key, topic.strip().lower())

        if key in seen:
            raise RuntimeError("Gemini returned duplicate topic candidates")
        seen.add(key)

        if exam_key not in allowed_exams:
            raise RuntimeError(f"Invalid exam in topic candidate: {exam}")
        if subject_key not in allowed_subjects:
            raise RuntimeError(f"Invalid subject in topic candidate: {subject}")

        if not isinstance(indices, list) or not indices:
            raise RuntimeError(f"Topic candidate has no supporting signals: {topic}")
        if len(indices) != len(set(indices)):
            raise RuntimeError(f"Topic candidate repeats a supporting signal: {topic}")
        if any(
            not isinstance(index, int) or not 0 <= index < len(signals)
            for index in indices
        ):
            raise RuntimeError(f"Topic candidate has invalid signal indices: {topic}")

        scores: dict[str, int] = {}
        for field in (
            "exam_relevance",
            "novelty",
            "educational_value",
            "visual_potential",
            "production_reliability",
        ):
            value = candidate.get(field)
            if not isinstance(value, int) or not 0 <= value <= 100:
                raise RuntimeError(f"Invalid {field} for topic candidate: {topic}")
            scores[field] = value

        if not clean_titles:
            scores["novelty"] = 50

        rationale = candidate.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            raise RuntimeError(f"Missing rationale for topic candidate: {topic}")

        demand = round(
            sum(demand_scores[index] for index in indices) / len(indices),
            2,
        )
        total = round(
            demand * _SCORE_WEIGHTS["demand"]
            + scores["exam_relevance"] * _SCORE_WEIGHTS["exam_relevance"]
            + scores["novelty"] * _SCORE_WEIGHTS["novelty"]
            + scores["educational_value"] * _SCORE_WEIGHTS["educational_value"]
            + scores["visual_potential"] * _SCORE_WEIGHTS["visual_potential"]
            + scores["production_reliability"] * _SCORE_WEIGHTS["production_reliability"],
            2,
        )

        results.append(
            TopicScore(
                exam=allowed_exams[exam_key],
                subject=allowed_subjects[subject_key],
                topic=topic.strip(),
                demand_score=demand,
                exam_relevance=scores["exam_relevance"],
                novelty=scores["novelty"],
                educational_value=scores["educational_value"],
                visual_potential=scores["visual_potential"],
                production_reliability=scores["production_reliability"],
                total_score=total,
                supporting_signal_indices=tuple(indices),
                rationale=rationale.strip(),
            )
        )

    return sorted(results, key=lambda item: item.total_score, reverse=True)
