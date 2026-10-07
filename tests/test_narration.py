import json

import pytest

import narration


class FakeCommunicate:
    calls = []

    def __init__(self, text, voice, *, rate, volume, pitch, **kwargs):
        self.calls.append((text, voice, rate, volume, pitch, kwargs))

    async def save(self, path):
        with open(path, "wb") as file:
            file.write(b"fake-audio")


def test_synthesize_speech_uses_default_hindi_voice(monkeypatch, tmp_path):
    FakeCommunicate.calls = []
    monkeypatch.setattr(narration.edge_tts, "Communicate", FakeCommunicate)
    monkeypatch.setattr(narration, "TTS_VOICE", "")

    output = narration.synthesize_speech(
        "Aaj ka practice question percentages par hai.",
        tmp_path / "audio.mp3",
    )

    assert output.exists()
    assert output.read_bytes() == b"fake-audio"
    assert FakeCommunicate.calls == [
        (
            "Aaj ka practice question percentages par hai.",
            "hi-IN-MadhurNeural",
            "+0%",
            "+0%",
            "+0Hz",
            {},
        )
    ]


def test_synthesize_speech_uses_configured_voice(monkeypatch, tmp_path):
    FakeCommunicate.calls = []
    monkeypatch.setattr(narration.edge_tts, "Communicate", FakeCommunicate)
    monkeypatch.setattr(narration, "TTS_VOICE", "hi-IN-SwaraNeural")

    narration.synthesize_speech("Test narration.", tmp_path / "voice.mp3")

    assert FakeCommunicate.calls[0][1] == "hi-IN-SwaraNeural"


def test_synthesize_speech_accepts_explicit_voice_and_audio_settings(monkeypatch, tmp_path):
    FakeCommunicate.calls = []
    monkeypatch.setattr(narration.edge_tts, "Communicate", FakeCommunicate)

    narration.synthesize_speech(
        "Question ka answer dekhiye.",
        tmp_path / "custom.mp3",
        voice="hi-IN-MadhurNeural",
        rate="-10%",
        volume="+10%",
        pitch="+2Hz",
    )

    assert FakeCommunicate.calls[0] == (
        "Question ka answer dekhiye.",
        "hi-IN-MadhurNeural",
        "-10%",
        "+10%",
        "+2Hz",
        {},
    )


def test_synthesize_speech_with_timing_streams_audio_and_word_boundaries(
    monkeypatch,
    tmp_path,
):
    events = [
        {"type": "WordBoundary", "offset": 0, "duration": 4_000_000, "text": "Aaj"},
        {"type": "audio", "data": b"aa"},
        {"type": "WordBoundary", "offset": 4_000_000, "duration": 3_000_000, "text": "test"},
        {"type": "audio", "data": b"bb"},
    ]

    class StreamingCommunicate:
        def __init__(self, text, voice, *, rate, volume, pitch, boundary):
            assert text == "Aaj test"
            assert voice == "hi-IN-MadhurNeural"
            assert boundary == "WordBoundary"

        async def stream(self):
            for event in events:
                yield event

    monkeypatch.setattr(narration.edge_tts, "Communicate", StreamingCommunicate)

    output = narration.synthesize_speech(
        "Aaj test",
        tmp_path / "audio.mp3",
        timing_path=tmp_path / "timing.json",
    )

    assert output.read_bytes() == b"aabb"
    payload = json.loads((tmp_path / "timing.json").read_text(encoding="utf-8"))
    assert payload["text"] == "Aaj test"
    assert payload["duration_seconds"] == 0.7
    assert payload["words"] == [
        {"text": "Aaj", "start_seconds": 0.0, "duration_seconds": 0.4},
        {"text": "test", "start_seconds": 0.4, "duration_seconds": 0.3},
    ]


def test_synthesize_speech_rejects_empty_text():
    with pytest.raises(ValueError, match="text must not be empty"):
        narration.synthesize_speech("   ", "output.mp3")


def test_synthesize_speech_fails_when_no_audio_is_written(monkeypatch, tmp_path):
    class NoOutputCommunicate(FakeCommunicate):
        async def save(self, path):
            return None

    monkeypatch.setattr(narration.edge_tts, "Communicate", NoOutputCommunicate)

    with pytest.raises(RuntimeError, match="no audio"):
        narration.synthesize_speech("Hello.", tmp_path / "missing.mp3")


def test_synthesize_speech_fails_when_no_word_boundaries(monkeypatch, tmp_path):
    class NoTimingCommunicate:
        def __init__(self, *args, **kwargs):
            pass

        async def stream(self):
            yield {"type": "audio", "data": b"fake-audio"}

    monkeypatch.setattr(narration.edge_tts, "Communicate", NoTimingCommunicate)

    with pytest.raises(RuntimeError, match="no word timing"):
        narration.synthesize_speech(
            "Hello.",
            tmp_path / "audio.mp3",
            timing_path=tmp_path / "timing.json",
        )


def test_synthesize_speech_allows_overlapping_word_spans(monkeypatch, tmp_path):
    events = [
        {"type": "WordBoundary", "offset": 0, "duration": 4_000_000, "text": "Aaj"},
        {"type": "WordBoundary", "offset": 3_000_000, "duration": 3_000_000, "text": "test"},
    ]

    class StreamingCommunicate:
        def __init__(self, *args, **kwargs):
            pass

        async def stream(self):
            for event in events:
                yield event

    monkeypatch.setattr(narration.edge_tts, "Communicate", StreamingCommunicate)

    output = narration.synthesize_speech(
        "Aaj test",
        tmp_path / "audio.mp3",
        timing_path=tmp_path / "timing.json",
    )

    assert output.exists()
    payload = json.loads((tmp_path / "timing.json").read_text(encoding="utf-8"))
    assert payload["words"][1]["start_seconds"] == 0.3
