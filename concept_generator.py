from __future__ import annotations

import json
import time
from typing import Any

import requests

from config import GEMINI_API_KEY, GEMINI_MODEL, validate_config

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "concept_summary": {"type": "string"},
    },
    "required": ["concept_summary"],
}


def generate_concept_summary(
    *,
    subject: str,
    exam: str,
    topic: str,
    language: str = "Hinglish",
) -> str:
    for name, value in (
        ("subject", subject),
        ("exam", exam),
        ("topic", topic),
        ("language", language),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")

    validate_config(require_gemini=True)

    prompt = f"""
Create the concise teaching concept for one Indian competitive-exam lesson.

Exam: {exam}
Subject: {subject}
Topic: {topic}
Output language: {language}

Write one self-contained concept explanation that a learner can understand before practice.
Teach the underlying rule or idea, not a generic definition.
Include the key formula, condition, distinction, or reasoning rule when the topic needs one.
Do not include practice questions, answer choices, fabricated exam statistics, dates, guarantees, or citations.
Keep it concise enough for an instructional video card.

Return only structured JSON.
""".strip()

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        "You are the concept-teaching engine for an Indian competitive-exam "
                        "education channel. Be precise, useful, and concise. Never invent "
                        "exam-specific facts."
                    )
                }
            ]
        },
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseFormat": {
                "text": {
                    "mimeType": "application/json",
                    "schema": _RESPONSE_SCHEMA,
                }
            },
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
            f"Gemini concept generation failed ({response.status_code}): "
            f"{response.text[:500]}"
        )

    try:
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
        summary = data["concept_summary"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Gemini returned an invalid structured concept response") from exc

    if not isinstance(summary, str) or not summary.strip():
        raise RuntimeError("Gemini returned an empty concept summary")

    return summary.strip()
