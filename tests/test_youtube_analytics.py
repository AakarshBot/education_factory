from datetime import date, datetime, timezone

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
            {"name": "engagedViews"},
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
                ["video1", "120", "110", "40.5", "95", "70.5", "12", "3", "4"],
                ["video2", "30", "25", "10", "80", "60", "4", "1", "1"],
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
    assert result["video1"]["engagedViews"] == 110
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
        response([["video1", "1", "1", "1", "1", "1", "1", "1", "1"]])
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
        response([["video1", "120", "110", "40.5", "95", "70.5", "12", "3", "4"]])
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



class FakeVideosRequest:
    def __init__(self, body=None, error=None):
        self.body = body
        self.error = error

    def execute(self):
        if self.error:
            raise self.error
        return self.body


class FakeVideos:
    def __init__(self, body=None, error=None):
        self.body = body
        self.error = error
        self.calls = []

    def list(self, **kwargs):
        self.calls.append(kwargs)
        return FakeVideosRequest(self.body, self.error)


class FakeChannelsRequest:
    def __init__(self, body):
        self.body = body

    def execute(self):
        return self.body


class FakeChannels:
    def __init__(self, body):
        self.body = body
        self.calls = []

    def list(self, **kwargs):
        self.calls.append(kwargs)
        return FakeChannelsRequest(self.body)


class FakePlaylistRequest:
    def __init__(self, body):
        self.body = body

    def execute(self):
        return self.body


class FakePlaylistItems:
    def __init__(self, body):
        self.body = body
        self.calls = []

    def list(self, **kwargs):
        self.calls.append(kwargs)
        return FakePlaylistRequest(self.body)


class FakeYouTube:
    def __init__(self, body=None, error=None, channel_body=None, playlist_body=None):
        self.videos_api = FakeVideos(body, error)
        self.channels_api = FakeChannels(channel_body or {"items": []})
        self.playlist_api = FakePlaylistItems(playlist_body or {"items": []})

    def videos(self):
        return self.videos_api

    def channels(self):
        return self.channels_api

    def playlistItems(self):
        return self.playlist_api


def test_fetch_video_statistics_uses_current_data_api_counters():
    youtube = FakeYouTube(
        {
            "items": [
                {
                    "id": "video1",
                    "snippet": {"publishedAt": "2026-10-08T18:30:00Z"},
                    "statistics": {"viewCount": "123", "likeCount": "9", "commentCount": "2"},
                    "status": {"privacyStatus": "public"},
                }
            ]
        }
    )
    result = youtube_analytics.fetch_video_statistics(youtube, ["video1"])
    assert result["video1"] == {
        "title": "",
        "publishedAt": "2026-10-08T18:30:00Z",
        "views": 123,
        "likes": 9,
        "comments": 2,
        "privacyStatus": "public",
        "publishAt": None,
    }
    assert youtube.videos_api.calls == [
        {"part": "snippet,statistics,status", "id": "video1"}
    ]


def test_snapshot_uses_current_counters_and_does_not_write_history(tmp_path):
    history = tmp_path / "history.json"
    save_history(
        [
            entry("video1", "Syllogism"),
            HistoryEntry(
                exam="SSC",
                subject="Maths",
                topic="Percentages",
                lesson_type="practice",
                title="Percentages Practice",
                status="published",
                created_at="2026-10-08T00:00:00Z",
                video_id="video2",
                published_at="2026-10-08T12:00:00Z",
                metrics={},
                content_format="shorts",
            ),
        ],
        history,
    )
    youtube = FakeYouTube(
        {
            "items": [
                {"id": "video1", "snippet": {"title": "Syllogism Practice", "publishedAt": "2026-10-08T00:00:00Z"}, "statistics": {"viewCount": "120"}, "status": {"privacyStatus": "public"}},
                {"id": "video2", "snippet": {"publishedAt": "2026-10-08T12:00:00Z"}, "statistics": {"viewCount": "60"}},
            ]
        },
        channel_body={
            "items": [
                {"contentDetails": {"relatedPlaylists": {"uploads": "UUuploads"}}}
            ]
        },
        playlist_body={
            "items": [
                {"contentDetails": {"videoId": "video1"}},
                {"contentDetails": {"videoId": "video2"}},
            ]
        },
    )
    analytics = FakeAnalytics(
        response(
            [
                ["video1", "100", "90", "20", "60", "50", "8", "1", "2"],
                ["video2", "50", "45", "10", "30", "75", "4", "0", "1"],
            ]
        )
    )
    before = history.read_text(encoding="utf-8")
    snapshot, end_date = youtube_analytics._snapshot(
        history,
        limit=10,
        days=30,
        youtube=youtube,
        youtube_analytics=analytics,
        now=datetime(2026, 10, 10, tzinfo=timezone.utc),
    )
    assert snapshot[0]["content_format"] == "shorts"
    assert snapshot[0]["views"] == 60
    assert snapshot[0]["engaged_views"] == 45
    assert snapshot[0]["average_view_percentage"] == 75
    assert snapshot[1]["age_hours"] == 48
    assert end_date.isoformat() == "2026-10-08"
    assert history.read_text(encoding="utf-8") == before


def test_fetch_video_statistics_keeps_scheduled_visibility():
    youtube = FakeYouTube(
        {
            "items": [
                {
                    "id": "video1",
                    "snippet": {"publishedAt": "2026-10-08T12:30:00Z"},
                    "statistics": {},
                    "status": {
                        "privacyStatus": "private",
                        "publishAt": "2026-10-09T00:30:00Z",
                    },
                }
            ]
        }
    )
    result = youtube_analytics.fetch_video_statistics(youtube, ["video1"])
    assert result["video1"]["privacyStatus"] == "private"
    assert result["video1"]["publishAt"] == "2026-10-09T00:30:00Z"



def test_snapshot_uses_channel_uploads_and_reports_missing_history(tmp_path):
    history = tmp_path / "history.json"
    save_history([entry("video1", "Syllogism"), entry("missing", "Missing")], history)
    youtube = FakeYouTube(
        body={
            "items": [
                {
                    "id": "video1",
                    "snippet": {
                        "title": "Syllogism Practice",
                        "publishedAt": "2026-10-08T00:00:00Z",
                    },
                    "statistics": {"viewCount": "120", "likeCount": "8", "commentCount": "1"},
                    "status": {"privacyStatus": "public"},
                }
            ]
        },
        channel_body={
            "items": [
                {
                    "contentDetails": {
                        "relatedPlaylists": {"uploads": "UUuploads"},
                    }
                }
            ]
        },
        playlist_body={
            "items": [{"contentDetails": {"videoId": "video1"}}]
        },
    )
    analytics = FakeAnalytics(response([]))
    snapshot, _, missing = youtube_analytics._snapshot(
        history,
        limit=10,
        days=30,
        youtube=youtube,
        youtube_analytics=analytics,
        now=datetime(2026, 10, 10, tzinfo=timezone.utc),
    )
    assert [item["video_id"] for item in snapshot] == ["video1"]
    assert missing == ["missing"]
    assert youtube.channels_api.calls == [{"part": "contentDetails", "mine": True}]
    assert youtube.playlist_api.calls[0]["playlistId"] == "UUuploads"



def test_fetch_recent_channel_videos_enumerates_uploads():
    youtube = FakeYouTube(
        body={
            "items": [
                {
                    "id": "video1",
                    "snippet": {"title": "Syllogism Practice", "publishedAt": "2026-10-08T00:00:00Z"},
                    "statistics": {"viewCount": "120"},
                    "status": {"privacyStatus": "public"},
                }
            ]
        },
        channel_body={"items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UUuploads"}}}]},
        playlist_body={"items": [{"contentDetails": {"videoId": "video1"}}]},
    )
    result = youtube_analytics.fetch_recent_channel_videos(youtube, 10)
    assert result == [{
        "video_id": "video1",
        "title": "Syllogism Practice",
        "publishedAt": "2026-10-08T00:00:00Z",
        "views": 120,
        "likes": None,
        "comments": None,
        "privacyStatus": "public",
        "publishAt": None,
    }]
