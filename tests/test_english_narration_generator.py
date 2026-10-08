import json

import pytest

import english_narration_generator


class FakeResponse:
    def __init__(self, status_code=200, body=None, text=""):
        self.status_code = status_code
        self._body = body
        self.text = text

    def json(self):
        return self._body


def _patch(monkeypatch, source, translated):
    monkeypatch.setattr(english_narration_generator, "validate_config", lambda **_: None)
    monkeypatch.setattr(english_narration_generator, "GEMINI_API_KEY", "test-key")

    _, replacements = english_narration_generator._mask_segments(source)
    protected = []
    for translated_segment, segment_replacements in zip(translated, replacements):
        value = translated_segment
        for placeholder, original in segment_replacements:
            value = value.replace(original, placeholder)
        protected.append(value)

    def fake_post(url, **kwargs):
        return FakeResponse(
            body={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": json.dumps({"segments": protected})}
                            ]
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(english_narration_generator.requests, "post", fake_post)


def test_generate_english_narration_preserves_segment_count_and_order(monkeypatch):
    source = [
        "Question 1. 25% of 240 is? Options: A. 60 B. 70 C. 80 D. 90.",
        "The correct answer is 60.",
        "25 percent is one fourth, so 240 divided by 4 is 60.",
    ]
    translated = [
        "Question 1. What is 25% of 240? Options: A. 60 B. 70 C. 80 D. 90.",
        "The correct answer is 60.",
        "25 percent is one fourth, so 240 divided by 4 is 60.",
    ]
    _patch(monkeypatch, source, translated)

    result = english_narration_generator.generate_english_narration_segments(source)

    assert result == translated


def test_generate_english_narration_uses_structured_json(monkeypatch):
    source = ["Question 1. Solve this."]
    _patch(monkeypatch, source, ["Question 1. Solve this."])

    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs)
        return FakeResponse(
            body={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": json.dumps({"segments": ["Question 1. Solve this."]})}
                            ]
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(english_narration_generator.requests, "post", fake_post)

    result = english_narration_generator.generate_english_narration_segments(source)

    assert result == source
    config = calls[0]["json"]["generationConfig"]
    assert config["responseFormat"]["text"]["mimeType"] == "APPLICATION_JSON"
    assert config["responseFormat"]["text"]["schema"]["properties"]["segments"]["type"] == "array"


def test_generate_english_narration_rejects_wrong_segment_count(monkeypatch):
    source = ["Question 1. Solve this.", "The answer is 5."]
    _patch(monkeypatch, source, ["Question 1. Solve this."])

    with pytest.raises(RuntimeError, match="exactly one"):
        english_narration_generator.generate_english_narration_segments(source)


def test_generate_english_narration_rejects_empty_input(monkeypatch):
    with pytest.raises(ValueError, match="must not be empty"):
        english_narration_generator.generate_english_narration_segments([])


def test_generate_english_narration_rejects_http_failure(monkeypatch):
    monkeypatch.setattr(english_narration_generator, "validate_config", lambda **_: None)
    monkeypatch.setattr(english_narration_generator, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        english_narration_generator.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(status_code=429, text="rate limited"),
    )

    with pytest.raises(RuntimeError, match="generation failed"):
        english_narration_generator.generate_english_narration_segments(
            ["Question 1. Solve this."]
        )


def test_generate_english_narration_rejects_changed_numeric_content(monkeypatch):
    source = ["Question 1. 25% of 240 is? Options: A. 60 B. 70 C. 80 D. 90."]
    _patch(
        monkeypatch,
        source,
        ["Question 1. What is 25% of 250? Options: A. 60 B. 70 C. 80 D. 90."],
    )
    with pytest.raises(RuntimeError, match="protected content"):
        english_narration_generator.generate_english_narration_segments(source)


def test_generate_english_narration_rejects_changed_answer(monkeypatch):
    source = ["The correct answer is 60."]
    _patch(monkeypatch, source, ["The correct answer is 70."])
    with pytest.raises(RuntimeError, match="protected content"):
        english_narration_generator.generate_english_narration_segments(source)


def test_generate_english_narration_restores_protected_numbers(monkeypatch):
    source = [
        "Question 1. 25% of 240 is? Options: A. 60 B. 70 C. 80 D. 90.",
    ]
    masked, _ = english_narration_generator._mask_segments(source)
    translated = [
        masked[0].replace("[[NUMBER_B]]%", "[[NUMBER_B]] percent"),
    ]
    _patch(monkeypatch, source, translated)

    result = english_narration_generator.generate_english_narration_segments(source)

    assert result[0] == "Question 1. 25 percent of 240 is? Options: A. 60 B. 70 C. 80 D. 90."


def test_generate_english_narration_rejects_missing_protected_token(monkeypatch):
    source = ["Question 1. 25% of 240 is?"]
    _patch(monkeypatch, source, ["What is 25% of 240?"])
    with pytest.raises(RuntimeError, match="protected content"):
        english_narration_generator.generate_english_narration_segments(source)


def test_generate_english_narration_allows_language_only_translation(monkeypatch):
    source = [
        "Question 1. 25% of 240 is? Options: A. 60 B. 70 C. 80 D. 90.",
        "The correct answer is 60.",
    ]
    translated = [
        "Question 1. What is 25% of 240? Options: A. 60 B. 70 C. 80 D. 90.",
        "The correct answer is 60.",
    ]
    _patch(monkeypatch, source, translated)
    assert english_narration_generator.generate_english_narration_segments(source) == translated
