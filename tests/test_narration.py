import pytest

import narration


class FakeCommunicate:
    calls = []

    def __init__(self, text, voice, *, rate, volume, pitch):
        self.calls.append((text, voice, rate, volume, pitch))

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
    )


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
