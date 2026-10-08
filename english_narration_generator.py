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
_PROTECTED_TOKEN_PATTERN = re.compile(r"\[\[(?:NUMBER|ANSWER|OPTIONS)_[A-Z]+\]\]")


def _numeric_tokens(text: str) -> list[str]:
    return [token.replace(",", "") for token in _NUMERIC_TOKEN_PATTERN.findall(text)]


def _answer_value(text: str) -> str | None:
    match = _ANSWER_PATTERN.search(text)
    return match.group(1).strip() if match else None


def _token_suffix(index: int) -> str:
    value = index + 1
    suffix = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        suffix = chr(65 + remainder) + suffix
    return suffix


def _mask_invariants(segment: str) -> tuple[str, list[tuple[str, str]]]:
    spans = []

    answer = _ANSWER_PATTERN.search(segment)
    if answer:
        spans.append((answer.start(1), answer.end(1), "ANSWER", answer.group(1).strip()))

    for match in re.finditer(re.escape("Options:"), segment):
        if not any(start <= match.start() < end for start, end, _, _ in spans):
            spans.append((match.start(), match.end(), "OPTIONS", match.group(0)))

    for match in _NUMERIC_TOKEN_PATTERN.finditer(segment):
        if not any(start <= match.start() < end for start, end, _, _ in spans):
            spans.append((match.start(), match.end(), "NUMBER", match.group(0)))

    spans.sort(key=lambda item: item[0])

    masked_parts = []
    replacements = []
    cursor = 0
    for index, (start, end, kind, original) in enumerate(spans):
        masked_parts.append(segment[cursor:start])
        placeholder = f"[[{kind}_{_token_suffix(index)}]]"
        masked_parts.append(placeholder)
        replacements.append((placeholder, original))
        cursor = end
    masked_parts.append(segment[cursor:])
    return "".join(masked_parts), replacements


def _mask_segments(segments: list[str]) -> tuple[list[str], list[list[tuple[str, str]]]]:
    masked_segments = []
    replacements = []
    for segment in segments:
        masked, segment_replacements = _mask_invariants(segment)
        masked_segments.append(masked)
        replacements.append(segment_replacements)
    return masked_segments, replacements


def _restore_invariants(
    translated: list[str],
    replacements: list[list[tuple[str, str]]],
) -> list[str]:
    restored = []
    for index, (segment, segment_replacements) in enumerate(zip(translated, replacements)):
        expected_tokens = [placeholder for placeholder, _ in segment_replacements]
        found_tokens = _PROTECTED_TOKEN_PATTERN.findall(segment)
        if found_tokens != expected_tokens:
            raise RuntimeError(
                f"English narration changed protected content in segment {index + 1}"
            )
        value = segment
        for placeholder, original in segment_replacements:
            value = value.replace(placeholder, original)
        restored.append(value)
    return restored


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

    masked_segments, replacements = _mask_segments(segments)

    prompt = f"""
Translate the following narration segments from {source_language} into natural, clear English for an Indian competitive-exam education video.

Rules:
- Return exactly {len(segments)} segments in exactly the same order.
- Preserve every question, option, answer, mathematical value, fact, and instruction.
- Do not add, remove, combine, split, or reinterpret information.
- Keep every protected token such as [[NUMBER_A]], [[ANSWER_B]], or [[OPTIONS_C]] exactly unchanged, including brackets, spelling, and order.
- Never spell out, translate, delete, duplicate, or reorder a protected token.
- Keep question numbering and option labels unchanged.
- Translate only the language, while preserving the instructional meaning.
- Use concise spoken English suitable for exam preparation.
- Do not add introductions, conclusions, opinions, or commentary.
- Return only the structured JSON object.

Source narration:
{json.dumps(masked_segments, ensure_ascii=False)}
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
    translated = _restore_invariants(translated, replacements)
    _validate_content_fidelity(segments, translated)
    return translated
