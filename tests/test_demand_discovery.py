import pytest

import demand_discovery


class FakeResponse:
    def __init__(self, status_code=200, body=None, text=""):
        self.status_code = status_code
        self._body = body
        self.text = text

    def json(self):
        return self._body


def test_default_queries_cover_locked_exams_and_subjects():
    assert len(demand_discovery.DEFAULT_DEMAND_QUERIES) == 9
    assert "SSC Maths 2026" in demand_discovery.DEFAULT_DEMAND_QUERIES
    assert "Banking Reasoning 2026" in demand_discovery.DEFAULT_DEMAND_QUERIES
    assert "Railway English 2026" in demand_discovery.DEFAULT_DEMAND_QUERIES


def test_discover_demand_collects_recent_and_popular_signals(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs["params"]))
        return FakeResponse(
            body={
                "items": [
                    {
                        "id": {"videoId": "abc123"},
                        "snippet": {
                            "title": "SSC Maths Percentage Questions 2026",
                            "channelTitle": "Example Channel",
                            "publishedAt": "2026-10-01T10:00:00Z",
                            "description": "Practice percentages for SSC.",
                        },
                    }
                ]
            }
        )

    monkeypatch.setattr(demand_discovery, "validate_config", lambda **_: None)
    monkeypatch.setattr(demand_discovery, "YOUTUBE_API_KEY", "test-key")
    monkeypatch.setattr(demand_discovery.requests, "get", fake_get)

    signals = demand_discovery.discover_demand(
        queries=["SSC Maths 2026"],
        days=30,
        max_results=10,
        region_code="IN",
    )

    assert len(signals) == 2
    assert {signal.order for signal in signals} == {"relevance", "viewCount"}
    assert signals[0].video_id == "abc123"
    assert signals[0].rank == 1
    assert len(calls) == 2
    for _, params in calls:
        assert params["part"] == "snippet"
        assert params["type"] == "video"
        assert params["key"] == "test-key"
        assert params["regionCode"] == "IN"
        assert params["publishedAfter"].endswith("Z")


def test_discover_demand_rejects_invalid_configuration(monkeypatch):
    monkeypatch.setattr(
        demand_discovery,
        "validate_config",
        lambda **_: (_ for _ in ()).throw(
            RuntimeError("Missing required configuration: YOUTUBE_API_KEY")
        ),
    )

    with pytest.raises(RuntimeError, match="YOUTUBE_API_KEY"):
        demand_discovery.discover_demand(queries=["SSC Maths 2026"])


def test_discover_demand_rejects_bad_arguments(monkeypatch):
    monkeypatch.setattr(demand_discovery, "validate_config", lambda **_: None)

    with pytest.raises(ValueError, match="must not be empty"):
        demand_discovery.discover_demand(queries=[])

    with pytest.raises(ValueError, match="between 1 and 50"):
        demand_discovery.discover_demand(queries=["SSC Maths"], max_results=51)

    with pytest.raises(ValueError, match="at least 1"):
        demand_discovery.discover_demand(queries=["SSC Maths"], days=0)

    with pytest.raises(ValueError, match="empty values"):
        demand_discovery.discover_demand(queries=["SSC Maths", ""])


def test_discover_demand_rejects_http_failure(monkeypatch):
    monkeypatch.setattr(demand_discovery, "validate_config", lambda **_: None)
    monkeypatch.setattr(demand_discovery, "YOUTUBE_API_KEY", "test-key")
    monkeypatch.setattr(
        demand_discovery.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(status_code=403, text="forbidden"),
    )

    with pytest.raises(RuntimeError, match="403"):
        demand_discovery.discover_demand(queries=["SSC Maths 2026"])
