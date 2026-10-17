from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

from config import GEMINI_API_KEY, GEMINI_MODEL, validate_config
from question import Question
from validators import ValidationError, validate_question

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "exam": {"type": "string"},
                    "topic": {"type": "string"},
                    "difficulty": {"type": "string"},
                    "question": {"type": "string"},
                    "choices": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "correct_choice_index": {"type": "integer", "minimum": 0, "maximum": 3},
                    "explanation": {"type": "string"},
                    "shortcut": {"type": ["string", "null"]},
                    "source_type": {"type": "string"},
                    "source_reference": {"type": ["string", "null"]},
                    "math_expression": {"type": ["string", "null"]},
                },
                "required": [
                    "subject",
                    "exam",
                    "topic",
                    "difficulty",
                    "question",
                    "choices",
                    "correct_choice_index",
                    "explanation",
                    "shortcut",
                    "source_type",
                    "source_reference",
                    "math_expression",
                ],
            },
        }
    },
    "required": ["questions"],
}



_VISUAL_REFERENCE_PATTERNS = (
    re.compile(
        r"\b(?:shown|displayed|provided|pictured|illustrated)\s+(?:below|above|here)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:in|from|of|according to|based on)\s+(?:the|this|following|given)\s+"
        r"(?:figure|diagram|chart|image|map|table)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the|this|following|given)\s+"
        r"(?:figure|diagram|chart|image|map|table)\s+"
        r"(?:shown|displayed|provided|pictured|illustrated|below|above)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:see|refer to|look at)\s+(?:the|this|following|given)\s+"
        r"(?:figure|diagram|chart|image|map|table)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:figure|diagram|chart|image|map|table)\s+"
        r"(?:shown|displayed|provided|pictured|illustrated)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:arrangement|pattern|sequence)\s+(?:shown|displayed|provided)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:as shown|as pictured|as illustrated|as displayed)\b",
        re.IGNORECASE,
    ),
)


def _normalize_math_expression(expression: str) -> str:
    if not isinstance(expression, str):
        return expression
    return expression.strip().replace("×", "*").replace("÷", "/").replace("^", "**")


def _validate_self_contained_text(question: str, choices: list[str]) -> None:
    search_text = " ".join([question, *choices])
    for pattern in _VISUAL_REFERENCE_PATTERNS:
        if pattern.search(search_text):
            raise ValidationError(
                "generated question depends on an unseen visual"
            )


def generate_questions(
    *,
    subject: str,
    exam: str,
    topic: str,
    difficulty: str,
    count: int,
    language: str = "Hinglish",
) -> list[Question]:
    if count < 1:
        raise ValueError("count must be at least 1")
    validate_config(require_gemini=True)

    prompt = f"""
Create exactly {count} original competitive-exam practice questions.

Exam: {exam}
Subject: {subject}
Topic: {topic}
Difficulty: {difficulty}
Output language: {language}

Rules:
- Create original questions, not copied previous-year questions.
- Every question must have exactly one defensible correct answer.
- Every question must be fully self-contained in text. Never require an unseen figure, diagram, chart, image, table, map, or visual prompt.
- Order the set as a deliberate learning progression, not a random list. Question 1 is the opening challenge: make it immediately understandable, exam-authentic, and compelling by testing a recognizable pattern or common misconception within the requested topic.
- Keep Question 1 approachable enough to attempt immediately. Do not front-load the hardest item, use trick wording, create ambiguity, or require hidden information.
- Let later questions progress from a core pattern to useful applications or harder variations. Vary the underlying method or pattern rather than repeating near-duplicate questions with changed numbers.
- Keep question stems concise and remove generic setup or filler that does not help solve the question.
- Do not refer to `given figure`, `shown below`, `in the diagram`, `from the image`, or any other missing visual. Describe all required information directly in the question.
- Every question must use exactly four unique choices.
- Set correct_choice_index to the zero-based index (0-3) of the correct choice.
- Keep the requested exam, subject, topic, and difficulty faithful.
- Set explanation to an empty string. Explanations are generated by the separate explanation stage.
- A shortcut may be null when no useful shortcut exists.
- source_type must be "original" and source_reference must be null.
- For Maths, math_expression is REQUIRED and must evaluate exactly to the choice at correct_choice_index.
- For Maths, all four choices must be numeric values only, with optional currency/percent/fraction notation such as `₹1,700`, `15%`, or `3/4`. Never append units, labels, or words to a Maths choice.
- For Maths, use only numbers, parentheses, +, -, *, /, and ** in math_expression. Do not use words, functions, factorials, percent signs, commas, ×, ÷, or ^; plain ASCII arithmetic is preferred.
- If math_expression uses **, its exponent must be an integer from -12 through 12. Prefer small powers only; never use a larger exponent. If a problem needs a larger power, use a different question with smaller values.
- For Maths, choose values with exact answers that can be represented by one of the four choices; avoid rounding and repeating-decimal ambiguity.
- For non-Maths questions, math_expression must be null.
- Do not put explanations or extra commentary outside the JSON object.

Return only the requested structured JSON.
""".strip()

    system_text = (
        "You are the question-writing engine for an Indian competitive-exam "
        "education channel. Accuracy is more important than creativity. "
        "Never invent an answer. Follow the requested schema exactly."
    )

    validation_error: ValidationError | None = None

    for generation_attempt in range(3):
        attempt_prompt = prompt
        if validation_error is not None:
            if "unsupported exponent" in str(validation_error).lower():
                correction = (
                    "The previous math_expression used an unsupported exponent. "
                    "Regenerate the complete question set using only integer exponents "
                    "from -12 through 12; rewrite any question needing a larger power "
                    "with smaller values. Recheck that each expression exactly matches "
                    "its selected numeric answer."
                )
            elif "not numeric" in str(validation_error).lower():
                correction = (
                    "The validation error identifies a Maths choice that is not numeric. "
                    "Correct that exact question and option. All four choices for every "
                    "Maths question must be numeric values only. Allowed formats include "
                    "1700, 1,700, ₹1,700, 15%, and 3/4. Never include words, units, labels, "
                    "equations, or explanations in a choice. Ensure correct_choice_index "
                    "selects a numeric value that exactly matches math_expression."
                )
            else:
                correction = (
                    "For Maths, every choice must be parseable as a numeric value; do not "
                    "append units, labels, or words to any Maths choice."
                )
            attempt_prompt += (
                "\n\nRETRY CORRECTION: The previous response failed deterministic "
                f"validation: {validation_error}. {correction}"
            )

        payload = {
            "systemInstruction": {"parts": [{"text": system_text}]},
            "contents": [{"parts": [{"text": attempt_prompt}]}],
            "generationConfig": {
                "responseFormat": {
                    "text": {
                        "mimeType": "APPLICATION_JSON",
                        "schema": _RESPONSE_SCHEMA,
                    },
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
                f"Gemini question generation failed ({response.status_code}): "
                f"{response.text[:500]}"
            )

        body = response.json()
        try:
            text = body["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(text)
            items = data["questions"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Gemini returned an invalid structured question response") from exc

        if len(items) != count:
            raise RuntimeError(
                f"Gemini returned {len(items)} questions; expected exactly {count}"
            )

        try:
            questions: list[Question] = []
            for item in items:
                item = dict(item)
                item["explanation"] = ""
                math_expression = _normalize_math_expression(item.pop("math_expression", None))
                correct_choice_index = item.pop("correct_choice_index", None)

                choices = item.get("choices")
                if (
                    not isinstance(choices, list)
                    or len(choices) != 4
                    or not all(isinstance(choice, str) and choice.strip() for choice in choices)
                    or not isinstance(correct_choice_index, int)
                    or not 0 <= correct_choice_index < 4
                ):
                    raise ValidationError("generated choices/correct_choice_index are invalid")

                question_text = item.get("question")
                if not isinstance(question_text, str) or not question_text.strip():
                    raise ValidationError("generated question text is invalid")
                _validate_self_contained_text(question_text, choices)

                item["correct_answer"] = choices[correct_choice_index]
                question = Question.from_dict(item)
                try:
                    validate_question(question, math_expression=math_expression)
                except ValidationError as exc:
                    raise ValidationError(
                        f"question {len(questions) + 1}: {exc}"
                    ) from exc
                questions.append(question)
        except ValidationError as exc:
            validation_error = exc
            if generation_attempt == 2:
                raise
            continue

        return questions

    raise RuntimeError("question generation failed deterministic validation")
