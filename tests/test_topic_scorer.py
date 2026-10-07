import json

import pytest

import topic_scorer
from demand_discovery import DemandSignal


def signals():
    return [
        DemandSignal(
            query="SSC Maths 2026",
            order="relevance",
            video_id="one",
            title="SSC CGL Percentage Questions",
            channel_title="A",
            published_at="2026-10-01T00:00:00Z",
            description="Percentage practice questions.",
            rank=1,
        ),
        DemandSignal(
            query="SSC Maths 2026",
            order="viewCount",
            video_id="two",
            title="SSC Maths Profit Loss Questions",
            channel_title="B",
            published_at="2026-10-01T00:00:00Z",
            description="Profit and loss practice.",
            rank=2,
        ),
        DemandSignal(
            query="Banking Reasoning 2026",
            order="relevance",
            video_id="three",
            title="Banking Syllogism Questions",
            channel_title="C",
            published_at="2026-10-01T00:00:00Z",
            description="Syllogism practice for banking exams.",
            rank=3,
        ),
    ]


def fake_candidate_response():
    return {
        "candidates": [
            {
                "exam": "SSC",
                "subject": "Maths",
                "topic": "Percentages",
                "signal_indices": [0],
                "exam_relevance": 95,
                "novelty": 80,
                "educational_value": 95,
                "visual_potential": 90,
                "production_reliability": 98,
                "rationale": "Percentages are directly teachable through worked exam questions.",
            },
            {
                "exam": "Banking",
                "subject": "Reasoning",
                "topic": "Syllogism",
                "signal_indices": [2],
                "exam_relevance": 92,
                "novelty": 75,
                "educational_value": 90,
                "visual_potential": 85,
                "production_reliability": 95,
                "rationale": "Syllogism supports clear step-by-step reasoning practice.",
            },
        ]
    }


class FakeResponse:
    status_code = 200
    text = ""

    def json(self):
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": json.dumps(fake_candidate_response())}]
                    }
                }
            ]
        }


def patch_gemini(monkeypatch, response_cls=FakeResponse):
    monkeypatch.setattr(topic_scorer, "validate_config", lambda **_: None)
    monkeypatch.setattr(topic_scorer, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        topic_scorer.requests,
        "post",
        lambda *args, **kwargs: response_cls(),
    )


def test_score_topics_calculates_demand_and_weighted_total(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["payload"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr(topic_scorer, "validate_config", lambda **_: None)
    monkeypatch.setattr(topic_scorer, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(topic_scorer.requests, "post", fake_post)

    result = topic_scorer.score_topics(
        signals(),
        recent_titles=["Old SSC Percentage Video"],
    )

    assert result[0].topic == "Percentages"
    assert result[0].demand_score == 100.0
    assert result[0].total_score == 93.8
    assert result[1].demand_score == 33.33
    config = captured["payload"]["generationConfig"]
    assert config["responseFormat"]["text"]["mimeType"] == "application/json"
    assert "responseSchema" not in config
    prompt = captured["payload"]["contents"][0]["parts"][0]["text"]
    assert "Old SSC Percentage Video" in prompt


def test_score_topics_uses_neutral_novelty_without_history(monkeypatch):
    patch_gemini(monkeypatch)

    result = topic_scorer.score_topics(signals())

    assert result[0].novelty == 50
    assert result[1].novelty == 50


def test_score_topics_retries_transient_failure(monkeypatch):
    class RetryResponse:
        def __init__(self, status_code):
            self.status_code = status_code
            self.text = "temporary"

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": json.dumps(fake_candidate_response())}]
                        }
                    }
                ]
            }

    responses = iter(
        [
            RetryResponse(503),
            RetryResponse(503),
            RetryResponse(200),
        ]
    )
    calls = []

    monkeypatch.setattr(topic_scorer, "validate_config", lambda **_: None)
    monkeypatch.setattr(topic_scorer, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        topic_scorer.requests,
        "post",
        lambda *args, **kwargs: (calls.append(True) or next(responses)),
    )
    delays = []
    monkeypatch.setattr(topic_scorer.time, "sleep", delays.append)

    result = topic_scorer.score_topics(signals())

    assert result
    assert len(calls) == 3
    assert delays == [1, 2]


def test_score_topics_rejects_bad_inputs(monkeypatch):
    patch_gemini(monkeypatch)

    with pytest.raises(ValueError, match="must not be empty"):
        topic_scorer.score_topics([])

    with pytest.raises(ValueError, match="positive"):
        topic_scorer.score_topics(
            [DemandSignal("q", "relevance", "v", "t", "c", "d", 0, 0)]
        )

    with pytest.raises(ValueError, match="empty values"):
        topic_scorer.score_topics(signals(), recent_titles=[""])


def test_score_topics_rejects_invalid_candidate(monkeypatch):
    class BadResponse(FakeResponse):
        def json(self):
            body = fake_candidate_response()
            body["candidates"][0]["exam"] = "UPSC"
            return {"candidates": [{"content": {"parts": [{"text": json.dumps(body)}]}}]}

    patch_gemini(monkeypatch, BadResponse)

    with pytest.raises(RuntimeError, match="Invalid exam"):
        topic_scorer.score_topics(signals())


def test_score_topics_rejects_duplicate_candidate(monkeypatch):
    class DuplicateResponse(FakeResponse):
        def json(self):
            body = fake_candidate_response()
            body["candidates"].append(dict(body["candidates"][0]))
            return {"candidates": [{"content": {"parts": [{"text": json.dumps(body)}]}}]}

    patch_gemini(monkeypatch, DuplicateResponse)

    with pytest.raises(RuntimeError, match="duplicate"):
        topic_scorer.score_topics(signals())


def test_score_topics_rejects_http_failure(monkeypatch):
    class ErrorResponse:
        status_code = 429
        text = "rate limited"

        def json(self):
            return {}

    monkeypatch.setattr(topic_scorer, "validate_config", lambda **_: None)
    monkeypatch.setattr(topic_scorer, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        topic_scorer.requests,
        "post",
        lambda *args, **kwargs: ErrorResponse(),
    )
    monkeypatch.setattr(topic_scorer.time, "sleep", lambda _: None)

    with pytest.raises(RuntimeError, match="429"):
        topic_scorer.score_topics(signals())
