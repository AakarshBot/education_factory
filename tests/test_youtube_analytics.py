from datetime import date

import pytest

import youtube_analytics
from channel_history import HistoryEntry, load_history, save_history


class FakeRequest:
    def __init__(self, body=None, error=None):
        self.body = body
        self.error = error

    def execute(self):
        if self.error:
            raise self.error
        return self.body


class FakeReports:
    def __init__(self, body=None, error=None):
        self.body = body
        self.error = error
        self.calls = []

    def query(self, **kwargs):
        self.calls.append(kwargs)
        return FakeRequest(self.body, self.error)


class FakeAnalytics:
    def __init__(self, body=None, error=None):
        self.reports_api = FakeReports(body, error)

    def reports(self):
        return self.reports_api


def response(rows):
    return {
        "columnHeaders": [
            {"name": "video"},
            {"name": "views"},
            {"name": "estimatedMinutesWatched"},
            {"name": "averageViewDuration"},
            {"name": "averageViewPercentage"},
            {"name": "likes"},
            {"name": "comments"},
            {"name": "subscribersGained"},
        ],
        "rows": rows,
    }


def entry(video_id, topic):
    return HistoryEntry(
        exam="SSC",
        subject="Maths",
        topic=topic,
        lesson_type="practice",
        title=f"{topic} Practice",
        status="published",
        created_at="2026-10-01T00:00:00Z",
        video_id=video_id,
        published_at="2026-10-01T00:00:00Z",
        metrics={},
    )


def test_fetch_video_metrics_builds_single_report_query():
    analytics = FakeAnalytics(
        response(
            [
                ["video1", "120", "40.5", "95", "70.5", "12", "3", "4"],
                ["video2", "30", "10", "80", "60", "4", "1", "1"],
            ]
        )
    )

    result = youtube_analytics.fetch_video_metrics(
        analytics,
        ["video1", "video2"],
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 7),
    )

    assert result["video1"]["views"] == 120
    assert result["video1"]["estimatedMinutesWatched"] == 40.5
    assert result["video1"]["averageViewPercentage"] == 70.5
    assert analytics.reports_api.calls[0] == {
        "ids": "channel==MINE",
        "startDate": "2026-10-01",
        "endDate": "2026-10-07",
        "metrics": youtube_analytics.METRICS,
        "dimensions": "video",
        "filters": "video==video1,video2",
    }


def test_fetch_video_metrics_batches_over_500_ids():
    analytics = FakeAnalytics(
        response([["video1", "1", "1", "1", "1", "1", "1", "1"]])
    )
    ids = [f"video{i}" for i in range(501)]
    result = youtube_analytics.fetch_video_metrics(
        analytics,
        ids,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 7),
    )
    assert len(analytics.reports_api.calls) == 2
    assert result["video1"]["views"] == 1


def test_ingest_metrics_updates_matching_history(tmp_path):
    history = tmp_path / "history.json"
    save_history([entry("video1", "Percentages"), entry("video2", "Ratios")], history)
    analytics = FakeAnalytics(
        response([["video1", "120", "40.5", "95", "70.5", "12", "3", "4"]])
    )

    updated = youtube_analytics.ingest_metrics(
        history_path=history,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 7),
        youtube_analytics=analytics,
    )

    assert updated[0].metrics["views"] == 120
    assert updated[1].metrics == {}
    assert load_history(history)[0].metrics["subscribersGained"] == 4


def test_ingest_metrics_uses_default_30_day_window(monkeypatch, tmp_path):
    history = tmp_path / "history.json"
    save_history([entry("video1", "Percentages")], history)
    analytics = FakeAnalytics(response([]))
    monkeypatch.setattr(
        youtube_analytics,
        "_default_window",
        lambda days: (date(2026, 9, 1), date(2026, 9, 30)),
    )

    youtube_analytics.ingest_metrics(
        history_path=history,
        youtube_analytics=analytics,
    )

    assert analytics.reports_api.calls[0]["startDate"] == "2026-09-01"
    assert analytics.reports_api.calls[0]["endDate"] == "2026-09-30"


def test_ingest_metrics_returns_empty_history_without_network(tmp_path, monkeypatch):
    history = tmp_path / "history.json"
    save_history([], history)

    def fail():
        raise AssertionError("analytics client should not be built")

    monkeypatch.setattr(youtube_analytics, "get_youtube_analytics_client", fail)
    assert youtube_analytics.ingest_metrics(history_path=history) == []


def test_fetch_video_metrics_rejects_bad_dates():
    analytics = FakeAnalytics(response([]))
    with pytest.raises(ValueError, match="after"):
        youtube_analytics.fetch_video_metrics(
            analytics,
            ["video1"],
            start_date=date(2026, 10, 7),
            end_date=date(2026, 10, 1),
        )


def test_fetch_video_metrics_rejects_duplicate_ids():
    analytics = FakeAnalytics(response([]))
    with pytest.raises(ValueError, match="unique"):
        youtube_analytics.fetch_video_metrics(
            analytics,
            ["video1", "video1"],
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 7),
        )


def test_fetch_video_metrics_fails_on_api_error():
    analytics = FakeAnalytics(error=RuntimeError("network"))
    with pytest.raises(RuntimeError, match="query failed"):
        youtube_analytics.fetch_video_metrics(
            analytics,
            ["video1"],
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 7),
        )


def test_fetch_video_metrics_fails_on_malformed_report():
    analytics = FakeAnalytics(body={"rows": []})
    with pytest.raises(RuntimeError, match="invalid report"):
        youtube_analytics.fetch_video_metrics(
            analytics,
            ["video1"],
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 7),
        )
