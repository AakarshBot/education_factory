import json

import pytest

import question_generator
from validators import ValidationError


class FakeResponse:
    def __init__(self, status_code=200, body=None, text=""):
        self.status_code = status_code
        self._body = body
        self.text = text

    def json(self):
        return self._body


def test_generate_questions_uses_structured_response_and_validates(monkeypatch):
    generated = {
        "questions": [
            {
                "subject": "maths",
                "exam": "SSC CGL",
                "topic": "percentages",
                "difficulty": "medium",
                "question": "A price of ₹2,000 is reduced by 15%. What is the selling price?",
                "choices": ["₹1,600", "₹1,700", "₹1,800", "₹1,900"],
                "correct_answer": "₹1,700",
                "explanation": "15% of ₹2,000 is ₹300, so ₹2,000 - ₹300 = ₹1,700.",
                "shortcut": "Multiply ₹2,000 by 0.85.",
                "source_type": "original",
                "source_reference": None,
                "math_expression": "2000 * (1 - 15 / 100)",
            }
        ]
    }

    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(
            body={
                "candidates": [
                    {"content": {"parts": [{"text": json.dumps(generated)}]}}
                ]
            }
        )

    monkeypatch.setattr(question_generator, "validate_config", lambda **_: None)
    monkeypatch.setattr(question_generator, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(question_generator.requests, "post", fake_post)

    result = question_generator.generate_questions(
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        difficulty="medium",
        count=1,
    )

    assert len(result) == 1
    assert result[0].correct_answer == "₹1,700"
    assert result[0].explanation == ""
    assert len(calls) == 1
    config = calls[0][1]["json"]["generationConfig"]
    assert config["responseFormat"]["text"]["mimeType"] == "application/json"
    assert "responseSchema" not in config
    assert config["responseFormat"]["text"]["schema"]["properties"]["choices"]["type"] == "array"
    assert config["responseFormat"]["text"]["schema"]["properties"]["choices"]["minItems"] == 4
    assert config["responseFormat"]["text"]["schema"]["properties"]["choices"]["maxItems"] == 4


def test_generate_questions_rejects_wrong_math_answer(monkeypatch):
    generated = {
        "questions": [
            {
                "subject": "maths",
                "exam": "SSC CGL",
                "topic": "percentages",
                "difficulty": "medium",
                "question": "A price of ₹2,000 is reduced by 15%. What is the selling price?",
                "choices": ["₹1,600", "₹1,700", "₹1,800", "₹1,900"],
                "correct_answer": "₹1,650",
                "explanation": "Incorrect answer.",
                "shortcut": None,
                "source_type": "original",
                "source_reference": None,
                "math_expression": "2000 * (1 - 15 / 100)",
            }
        ]
    }

    monkeypatch.setattr(question_generator, "validate_config", lambda **_: None)
    monkeypatch.setattr(question_generator, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        question_generator,
        "requests",
        type(
            "R",
            (),
            {
                "post": staticmethod(
                    lambda *args, **kwargs: FakeResponse(
                        body={
                            "candidates": [
                                {"content": {"parts": [{"text": json.dumps(generated)}]}}
                            ]
                        }
                    )
                )
            },
        ),
    )

    with pytest.raises(ValidationError, match="answer mismatch"):
        question_generator.generate_questions(
            subject="maths",
            exam="SSC CGL",
            topic="percentages",
            difficulty="medium",
            count=1,
        )


def test_generate_questions_requires_positive_count(monkeypatch):
    called = False

    def fake_validate(**_):
        nonlocal called
        called = True

    monkeypatch.setattr(question_generator, "validate_config", fake_validate)

    with pytest.raises(ValueError, match="at least 1"):
        question_generator.generate_questions(
            subject="maths",
            exam="SSC CGL",
            topic="percentages",
            difficulty="medium",
            count=0,
        )

    assert called is False


def test_generate_questions_rejects_http_failure(monkeypatch):
    monkeypatch.setattr(question_generator, "validate_config", lambda **_: None)
    monkeypatch.setattr(question_generator, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        question_generator,
        "requests",
        type(
            "R",
            (),
            {
                "post": staticmethod(
                    lambda *args, **kwargs: FakeResponse(
                        status_code=429, text="rate limited"
                    )
                )
            },
        ),
    )

    with pytest.raises(RuntimeError, match="429"):
        question_generator.generate_questions(
            subject="maths",
            exam="SSC CGL",
            topic="percentages",
            difficulty="medium",
            count=1,
        )
