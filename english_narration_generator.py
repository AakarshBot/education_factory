from __future__ import annotations

import json
import re
import time

import requests

from config import GEMINI_API_KEY, GEMINI_MODEL, validate_config

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "segments": {
            "type": "array",
            "items": {"type": "string"},
        }
    },
    "required": ["segments"],
}


_NUMERIC_TOKEN_PATTERN = re.compile(r"\d+(?:[,.]\d+)*(?:/\d+)?")
_ANSWER_PATTERN = re.compile(r"\bcorrect answer is\s+(.+?)(?:[.!?]|$)", re.IGNORECASE)


def _numeric_tokens(text: str) -> list[str]:
    return [token.replace(",", "") for token in _NUMERIC_TOKEN_PATTERN.findall(text)]


def _answer_value(text: str) -> str | None:
    match = _ANSWER_PATTERN.search(text)
    return match.group(1).strip() if match else None


def _validate_content_fidelity(source: list[str], translated: list[str]) -> None:
    for index, (source_segment, translated_segment) in enumerate(zip(source, translated)):
        if _numeric_tokens(source_segment) != _numeric_tokens(translated_segment):
            raise RuntimeError(
                f"English narration changed numeric content in segment {index + 1}"
            )

        source_answer = _answer_value(source_segment)
        if source_answer is not None:
            translated_answer = _answer_value(translated_segment)
            if translated_answer != source_answer:
                raise RuntimeError(
                    f"English narration changed the answer in segment {index + 1}"
                )

        if "Options:" in source_segment and "Options:" not in translated_segment:
            raise RuntimeError(
                f"English narration changed option structure in segment {index + 1}"
            )



def generate_english_narration_segments(
    segments: list[str],
    *,
    source_language: str = "Hinglish",
) -> list[str]:
    if not segments:
        raise ValueError("segments must not be empty")
    if any(not isinstance(segment, str) or not segment.strip() for segment in segments):
        raise ValueError("segments must contain only non-empty strings")
    if not source_language.strip():
        raise ValueError("source_language must not be empty")

    validate_config(require_gemini=True)

    prompt = f"""
Translate the following narration segments from {source_language} into natural, clear English for an Indian competitive-exam education video.

Rules:
- Return exactly {len(segments)} segments in exactly the same order.
- Preserve every question, option, answer, mathematical value, fact, and instruction.
- Do not add, remove, combine, split, or reinterpret information.
- Keep question numbering and option labels unchanged.
- Translate only the language, while preserving the instructional meaning.
- Use concise spoken English suitable for exam preparation.
- Do not add introductions, conclusions, opinions, or commentary.
- Return only the structured JSON object.

Source narration:
{json.dumps(segments, ensure_ascii=False)}
""".strip()

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        "You are an educational localization engine. "
                        "Translate faithfully without changing facts, answers, numbers, ordering, "
                        "or instructional structure."
                    )
                }
            ]
        },
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseFormat": {
                "text": {
                    "mimeType": "APPLICATION_JSON",
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
            f"English narration generation failed ({response.status_code}): "
            f"{response.text[:500]}"
        )

    try:
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
        translated = data["segments"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Gemini returned an invalid structured English narration response"
        ) from exc

    if (
        not isinstance(translated, list)
        or len(translated) != len(segments)
        or any(not isinstance(segment, str) or not segment.strip() for segment in translated)
    ):
        raise RuntimeError("English narration must contain exactly one non-empty segment per source segment")

    translated = [segment.strip() for segment in translated]
    _validate_content_fidelity(segments, translated)
    return translated
