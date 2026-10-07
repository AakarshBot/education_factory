import json

import pytest

import metadata_generator
from lesson import Lesson, LessonSegment
from question import Question


def lesson():
    q = Question(
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        difficulty="medium",
        question="25% of 240 is?",
        choices=("60", "70", "80", "90"),
        correct_answer="60",
        explanation="25 percent is one fourth.",
        shortcut="Divide by four.",
        source_type="original",
        source_reference=None,
    )
    return Lesson(
        lesson_type="practice",
        title="SSC CGL Maths Percentages Practice",
        subject="maths",
        exam="SSC CGL",
        topic="percentages",
        questions=(q,),
        segments=(
            LessonSegment(kind="question", question_index=0),
            LessonSegment(kind="answer", question_index=0),
        ),
    )


def response_payload(**overrides):
    data = {
        "title_candidates": [
            "SSC CGL Percentages: 10 Practice Questions",
            "Percentages Practice for SSC CGL Maths",
            "SSC CGL Maths Percentage Questions with Solutions",
            "Master Percentages with SSC CGL Practice",
            "SSC CGL Percentage Questions: Practice Session",
        ],
        "description": "Practice percentages for SSC CGL Maths with clear questions and explanations.",
        "hashtags": ["#SSCCGL", "#SSCMaths", "#Percentages"],
        "tags": ["SSC CGL Maths", "percentages questions", "SSC percentages"],
        "series_context": "SSC Maths Practice",
    }
    data.update(overrides)
    return {
        "candidates": [
            {"content": {"parts": [{"text": json.dumps(data, ensure_ascii=False)}]}}
        ]
    }


def patch(monkeypatch, body, status=200):
    class Response:
        status_code = status
        text = "error"

        def json(self):
            return body

    monkeypatch.setattr(metadata_generator.requests, "post", lambda *args, **kwargs: Response())


def test_generate_metadata_uses_first_title_as_primary(monkeypatch):
    monkeypatch.setattr(metadata_generator, "GEMINI_API_KEY", "key")
    patch(monkeypatch, response_payload())
    result = metadata_generator.generate_metadata(lesson())
    assert result.primary_title == result.title_candidates[0]
    assert len(result.title_candidates) == 5
    assert result.category_id == "27"
    assert result.default_language == "hi"


def test_generate_metadata_rejects_long_title(monkeypatch):
    monkeypatch.setattr(metadata_generator, "GEMINI_API_KEY", "key")
    patch(monkeypatch, response_payload(title_candidates=["x" * 101] * 5))
    with pytest.raises(RuntimeError, match="title exceeds"):
        metadata_generator.generate_metadata(lesson())


def test_generate_metadata_rejects_long_description(monkeypatch):
    monkeypatch.setattr(metadata_generator, "GEMINI_API_KEY", "key")
    patch(monkeypatch, response_payload(description="अ" * 2000))
    with pytest.raises(RuntimeError, match="description exceeds"):
        metadata_generator.generate_metadata(lesson())


def test_generate_metadata_rejects_unrelated_hashtag_format(monkeypatch):
    monkeypatch.setattr(metadata_generator, "GEMINI_API_KEY", "key")
    patch(monkeypatch, response_payload(hashtags=["#SSC CGL", "#Maths", "#Percentages"]))
    with pytest.raises(RuntimeError, match="must not contain spaces"):
        metadata_generator.generate_metadata(lesson())


def test_generate_metadata_rejects_urls(monkeypatch):
    monkeypatch.setattr(metadata_generator, "GEMINI_API_KEY", "key")
    patch(monkeypatch, response_payload(description="Learn at https://example.com"))
    with pytest.raises(RuntimeError, match="must not contain URLs"):
        metadata_generator.generate_metadata(lesson())


def test_generate_metadata_handles_http_failure(monkeypatch):
    monkeypatch.setattr(metadata_generator, "GEMINI_API_KEY", "key")
    patch(monkeypatch, response_payload(), status=429)
    with pytest.raises(RuntimeError, match="metadata generation failed"):
        metadata_generator.generate_metadata(lesson())
