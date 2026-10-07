import json

import pytest

import explanation_generator
from question import Question


def make_question():
    return Question(
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        difficulty="medium",
        question="A price of ₹2,000 is reduced by 15%. What is the selling price?",
        choices=("₹1,600", "₹1,700", "₹1,800", "₹1,900"),
        correct_answer="₹1,700",
        explanation="",
        shortcut="Multiply by 0.85.",
        source_type="original",
        source_reference=None,
    )


class FakeResponse:
    status_code = 200
    text = ""

    def json(self):
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "explanations": [
                                            {
                                                "index": 0,
                                                "explanation": (
                                                    "15% of ₹2,000 is ₹300. "
                                                    "Subtract ₹300 from ₹2,000 to get ₹1,700."
                                                ),
                                            }
                                        ]
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }


def test_generate_explanations_updates_only_explanation(monkeypatch):
    question = make_question()
    captured = {}

    def fake_post(url, **kwargs):
        captured["payload"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr(explanation_generator, "validate_config", lambda **_: None)
    monkeypatch.setattr(explanation_generator, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(explanation_generator.requests, "post", fake_post)

    result = explanation_generator.generate_explanations([question])

    assert result[0].explanation.startswith("15% of")
    assert result[0].correct_answer == question.correct_answer
    assert result[0].choices == question.choices
    assert result[0].question == question.question
    assert result[0].shortcut == question.shortcut
    assert captured["payload"]["generationConfig"]["responseMimeType"] == "application/json"
    sent_question = captured["payload"]["contents"][0]["parts"][0]["text"]
    assert '"verified_answer": "\u20b91,700"' in sent_question


def test_generate_explanations_ignores_attempted_answer_changes(monkeypatch):
    question = make_question()

    def fake_post(url, **kwargs):
        body = {
            "explanations": [
                {
                    "index": 0,
                    "explanation": (
                        "The calculation gives ₹1,700. The model may not change the answer."
                    ),
                    "correct_answer": "₹999",
                }
            ]
        }
        return type(
            "Response",
            (),
            {
                "status_code": 200,
                "text": "",
                "json": lambda self: {
                    "candidates": [
                        {"content": {"parts": [{"text": json.dumps(body)}]}}
                    ]
                },
            },
        )()

    monkeypatch.setattr(explanation_generator, "validate_config", lambda **_: None)
    monkeypatch.setattr(explanation_generator, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(explanation_generator.requests, "post", fake_post)

    result = explanation_generator.generate_explanations([question])

    assert result[0].correct_answer == "₹1,700"


def test_generate_explanations_rejects_missing_explanation(monkeypatch):
    class MissingResponse:
        status_code = 200
        text = ""

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps(
                                        {"explanations": [{"index": 0, "explanation": ""}]}
                                    )
                                }
                            ]
                        }
                    }
                ]
            }

    monkeypatch.setattr(explanation_generator, "validate_config", lambda **_: None)
    monkeypatch.setattr(explanation_generator, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        explanation_generator.requests, "post", lambda *args, **kwargs: MissingResponse()
    )

    with pytest.raises(RuntimeError, match="Missing explanation"):
        explanation_generator.generate_explanations([make_question()])


def test_generate_explanations_requires_questions():
    with pytest.raises(ValueError, match="must not be empty"):
        explanation_generator.generate_explanations([])
