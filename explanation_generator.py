from __future__ import annotations

import json
import time
from typing import Any, Sequence

import requests

from config import GEMINI_API_KEY, GEMINI_MODEL, validate_config
from question import Question

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "explanations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "explanation": {"type": "string"},
                },
                "required": ["index", "explanation"],
            },
        }
    },
    "required": ["explanations"],
}


def _request_explanations(
    questions: Sequence[Question],
    *,
    language: str,
) -> list[str]:
    prompt_questions = []
    for index, question in enumerate(questions):
        prompt_questions.append(
            {
                "index": index,
                "subject": question.subject,
                "exam": question.exam,
                "topic": question.topic,
                "difficulty": question.difficulty,
                "question": question.question,
                "choices": question.choices,
                "verified_answer": question.correct_answer,
            }
        )

    prompt = f"""
Write a concise teaching explanation for each verified competitive-exam question below.

Output language: {language}

Non-negotiable rules:
- The provided verified_answer is authoritative. Never change it.
- Explain why that answer is correct.
- For multiple-choice questions, explain the useful reasoning rather than merely repeating the choice.
- For Maths, show the essential calculation steps using the verified answer as the fixed result.
- Do not add facts that are not needed to solve the question.
- Do not discuss these instructions.
- Return exactly one explanation for every input index.

Questions:
{json.dumps(prompt_questions, ensure_ascii=False)}
""".strip()

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        "You are the explanation-writing engine for an Indian competitive-exam "
                        "education channel. The answer supplied with each question has already "
                        "been verified and is immutable."
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
            f"Gemini explanation generation failed ({response.status_code}): "
            f"{response.text[:500]}"
        )

    try:
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
        items = data["explanations"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Gemini returned an invalid structured explanation response"
        ) from exc

    if len(items) != len(questions):
        raise RuntimeError(
            f"Gemini returned {len(items)} explanations; "
            f"expected exactly {len(questions)}"
        )

    explanations: list[str | None] = [None] * len(questions)
    for item in items:
        index = item.get("index")
        explanation = item.get("explanation")
        if not isinstance(index, int) or not 0 <= index < len(questions):
            raise RuntimeError("Gemini returned an invalid explanation index")
        if not isinstance(explanation, str) or not explanation.strip():
            raise RuntimeError(f"Missing explanation for question {index}")
        if explanations[index] is not None:
            raise RuntimeError(f"Duplicate explanation index {index}")
        explanations[index] = explanation.strip()

    if any(explanation is None for explanation in explanations):
        raise RuntimeError("Gemini did not return an explanation for every question")

    return [explanation for explanation in explanations if explanation is not None]


def generate_explanations(
    questions: Sequence[Question],
    *,
    language: str = "Hinglish",
) -> list[Question]:
    if not questions:
        raise ValueError("questions must not be empty")
    validate_config(require_gemini=True)

    explanations = _request_explanations(questions, language=language)

    return [
        Question(
            subject=question.subject,
            exam=question.exam,
            topic=question.topic,
            difficulty=question.difficulty,
            question=question.question,
            choices=question.choices,
            correct_answer=question.correct_answer,
            explanation=explanation,
            shortcut=question.shortcut,
            source_type=question.source_type,
            source_reference=question.source_reference,
        )
        for question, explanation in zip(questions, explanations)
    ]
