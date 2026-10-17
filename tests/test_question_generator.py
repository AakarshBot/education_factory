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
                "correct_choice_index": 1,
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
    assert config["responseFormat"]["text"]["mimeType"] == "APPLICATION_JSON"
    assert "responseSchema" not in config
    choices_schema = config["responseFormat"]["text"]["schema"]["properties"]["questions"]["items"]["properties"]["choices"]
    assert choices_schema["type"] == "array"
    assert choices_schema["minItems"] == 4
    assert choices_schema["maxItems"] == 4
    prompt_text = calls[0][1]["json"]["contents"][0]["parts"][0]["text"]
    assert "Question 1 is the opening challenge" in prompt_text
    assert "Do not front-load the hardest item" in prompt_text
    assert "Vary the underlying method or pattern" in prompt_text
    assert "integer from -12 through 12" in prompt_text



def test_generate_questions_retries_deterministic_validation_failure(monkeypatch):
    invalid = {
        "questions": [{
            "subject": "maths",
            "exam": "SSC CGL",
            "topic": "percentages",
            "difficulty": "medium",
            "question": "A price of ₹2,000 is reduced by 15%. What is the selling price?",
            "choices": ["₹1,600", "₹1,700 students", "₹1,800", "₹1,900"],
            "correct_choice_index": 1,
            "explanation": "",
            "shortcut": None,
            "source_type": "original",
            "source_reference": None,
            "math_expression": "2000 * (1 - 15 / 100)",
        }]
    }
    valid = {
        "questions": [{
            "subject": "maths",
            "exam": "SSC CGL",
            "topic": "percentages",
            "difficulty": "medium",
            "question": "A price of ₹2,000 is reduced by 15%. What is the selling price?",
            "choices": ["₹1,600", "₹1,700", "₹1,800", "₹1,900"],
            "correct_choice_index": 1,
            "explanation": "",
            "shortcut": None,
            "source_type": "original",
            "source_reference": None,
            "math_expression": "2000 * (1 - 15 / 100)",
        }]
    }
    responses = iter((invalid, invalid, valid))
    prompts = []

    monkeypatch.setattr(question_generator, "validate_config", lambda **_: None)
    monkeypatch.setattr(question_generator, "GEMINI_API_KEY", "test-key")

    def fake_post(url, **kwargs):
        prompts.append(kwargs["json"]["contents"][0]["parts"][0]["text"])
        generated = next(responses)
        return FakeResponse(
            body={"candidates": [{"content": {"parts": [{"text": json.dumps(generated)}]}}]}
        )

    monkeypatch.setattr(question_generator.requests, "post", fake_post)

    result = question_generator.generate_questions(
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        difficulty="medium",
        count=1,
    )

    assert result[0].correct_answer == "₹1,700"
    assert len(prompts) == 3
    assert "RETRY CORRECTION" in prompts[1]
    assert "Maths choice 2 is not numeric" in prompts[1]
    assert "Correct that exact question and option" in prompts[1]
    assert "Maths choice 2 is not numeric" in prompts[2]


def test_generate_questions_repairs_unsupported_exponent(monkeypatch):
    def item(question, choices, answer_index, expression):
        return {
            "subject": "maths",
            "exam": "SSC CGL",
            "topic": "powers",
            "difficulty": "medium",
            "question": question,
            "choices": choices,
            "correct_choice_index": answer_index,
            "explanation": "",
            "shortcut": None,
            "source_type": "original",
            "source_reference": None,
            "math_expression": expression,
        }

    invalid = {
        "questions": [
            item("What is 2 raised to the power 13?", ["4096", "8192", "16384", "2048"], 1, "2 ** 13")
        ]
    }
    valid = {
        "questions": [
            item("What is 2 cubed?", ["6", "8", "4", "12"], 1, "2 ** 3")
        ]
    }
    responses = iter((invalid, valid))
    prompts = []

    monkeypatch.setattr(question_generator, "validate_config", lambda **_: None)
    monkeypatch.setattr(question_generator, "GEMINI_API_KEY", "test-key")

    def fake_post(url, **kwargs):
        prompts.append(kwargs["json"]["contents"][0]["parts"][0]["text"])
        generated = next(responses)
        return FakeResponse(
            body={"candidates": [{"content": {"parts": [{"text": json.dumps(generated)}]}}]}
        )

    monkeypatch.setattr(question_generator.requests, "post", fake_post)

    result = question_generator.generate_questions(
        subject="maths",
        exam="SSC CGL",
        topic="powers",
        difficulty="medium",
        count=1,
    )

    assert result[0].correct_answer == "8"
    assert len(prompts) == 2
    assert "unsupported exponent" in prompts[1]
    assert "integer exponents from -12 through 12" in prompts[1]

def test_normalizes_common_math_symbols(monkeypatch):
    generated = {
        "questions": [{
            "subject": "maths",
            "exam": "SSC CGL",
            "topic": "powers",
            "difficulty": "medium",
            "question": "What is 2 squared?",
            "choices": ["2", "4", "6", "8"],
            "correct_choice_index": 1,
            "explanation": "",
            "shortcut": None,
            "source_type": "original",
            "source_reference": None,
            "math_expression": "2 ^ 2",
        }]
    }

    monkeypatch.setattr(question_generator, "validate_config", lambda **_: None)
    monkeypatch.setattr(question_generator, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        question_generator.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(
            body={"candidates": [{"content": {"parts": [{"text": json.dumps(generated)}]}}]}
        ),
    )

    result = question_generator.generate_questions(
        subject="maths",
        exam="SSC CGL",
        topic="powers",
        difficulty="medium",
        count=1,
    )

    assert result[0].correct_answer == "4"


def test_generate_questions_rejects_unseen_visual_reference(monkeypatch):
    generated = {
        "questions": [
            {
                "subject": "reasoning",
                "exam": "SSC CGL",
                "topic": "counting of figures",
                "difficulty": "medium",
                "question": "In the diagram shown below, how many triangles are present?",
                "choices": ["4", "6", "8", "10"],
                "correct_choice_index": 1,
                "explanation": "This should be rejected before explanation generation.",
                "shortcut": None,
                "source_type": "original",
                "source_reference": None,
                "math_expression": None,
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

    with pytest.raises(ValidationError, match="unseen visual"):
        question_generator.generate_questions(
            subject="reasoning",
            exam="SSC CGL",
            topic="counting of figures",
            difficulty="medium",
            count=1,
        )


def test_generate_questions_allows_self_contained_figure_statement(monkeypatch):
    generated = {
        "questions": [
            {
                "subject": "reasoning",
                "exam": "SSC CGL",
                "topic": "figures",
                "difficulty": "medium",
                "question": "A five-sided figure is called a pentagon. Which shape has five sides?",
                "choices": ["Triangle", "Square", "Pentagon", "Circle"],
                "correct_choice_index": 2,
                "explanation": "A pentagon has five sides.",
                "shortcut": None,
                "source_type": "original",
                "source_reference": None,
                "math_expression": None,
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

    result = question_generator.generate_questions(
        subject="reasoning",
        exam="SSC CGL",
        topic="figures",
        difficulty="medium",
        count=1,
    )
    assert result[0].correct_answer == "Pentagon"


def test_generate_questions_rejects_math_choice_not_matching_expression(monkeypatch):
    generated = {
        "questions": [
            {
                "subject": "maths",
                "exam": "SSC CGL",
                "topic": "percentages",
                "difficulty": "medium",
                "question": "A price of ₹2,000 is reduced by 15%. What is the selling price?",
                "choices": ["₹1,600", "₹1,700", "₹1,800", "₹1,900"],
                "correct_choice_index": 0,
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
