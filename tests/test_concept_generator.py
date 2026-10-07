from types import SimpleNamespace

import pytest

import concept_generator


def test_generate_concept_summary_uses_structured_response(monkeypatch):
    monkeypatch.setattr(concept_generator, "GEMINI_API_KEY", "key")
    monkeypatch.setattr(concept_generator, "validate_config", lambda **kwargs: None)

    body = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"concept_summary":"25% means 25 parts out of 100, so divide by 4."}'
                        }
                    ]
                }
            }
        ]
    }

    response = SimpleNamespace(status_code=200, json=lambda: body)
    monkeypatch.setattr(concept_generator.requests, "post", lambda *args, **kwargs: response)

    assert concept_generator.generate_concept_summary(
        subject="Maths",
        exam="SSC",
        topic="Percentages",
    ) == "25% means 25 parts out of 100, so divide by 4."


def test_generate_concept_summary_rejects_empty_response(monkeypatch):
    monkeypatch.setattr(concept_generator, "GEMINI_API_KEY", "key")
    monkeypatch.setattr(concept_generator, "validate_config", lambda **kwargs: None)

    body = {
        "candidates": [
            {"content": {"parts": [{"text": '{"concept_summary":""}'}]}}
        ]
    }
    response = SimpleNamespace(status_code=200, json=lambda: body)
    monkeypatch.setattr(concept_generator.requests, "post", lambda *args, **kwargs: response)

    with pytest.raises(RuntimeError, match="empty concept"):
        concept_generator.generate_concept_summary(
            subject="Maths",
            exam="SSC",
            topic="Percentages",
        )


def test_generate_concept_summary_rejects_missing_topic():
    with pytest.raises(ValueError, match="topic"):
        concept_generator.generate_concept_summary(
            subject="Maths",
            exam="SSC",
            topic="",
        )
