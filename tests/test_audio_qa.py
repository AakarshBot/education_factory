import math
import struct
import wave

import pytest

from audio_qa import check_audio


def write_wav(path, *, duration=1.0, amplitude=10000):
    rate = 8000
    frames = int(rate * duration)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        for index in range(frames):
            value = int(amplitude * math.sin(2 * math.pi * 440 * index / rate))
            wav.writeframesraw(struct.pack("<h", value))


def test_check_audio_accepts_real_audio_and_validates_metadata(tmp_path):
    path = tmp_path / "tone.wav"
    write_wav(path)
    result = check_audio(path, expected_duration_seconds=1.0)
    assert result.duration_seconds == 1.0
    assert result.sample_rate == 8000
    assert result.channels == 1
    assert result.max_volume_db > -50


def test_check_audio_rejects_missing_file(tmp_path):
    with pytest.raises(RuntimeError, match="does not exist"):
        check_audio(tmp_path / "missing.wav")


def test_check_audio_rejects_empty_file(tmp_path):
    path = tmp_path / "empty.wav"
    path.write_bytes(b"")
    with pytest.raises(RuntimeError, match="empty"):
        check_audio(path)


def test_check_audio_rejects_silence(tmp_path):
    path = tmp_path / "silence.wav"
    write_wav(path, amplitude=0)
    with pytest.raises(RuntimeError, match="silence only"):
        check_audio(path)


def test_check_audio_rejects_short_audio(tmp_path):
    path = tmp_path / "short.wav"
    write_wav(path, duration=0.05)
    with pytest.raises(RuntimeError, match="too short"):
        check_audio(path)


def test_check_audio_rejects_duration_mismatch(tmp_path):
    path = tmp_path / "tone.wav"
    write_wav(path, duration=1.0)
    with pytest.raises(RuntimeError, match="duration mismatch"):
        check_audio(path, expected_duration_seconds=3.0)


def test_check_audio_rejects_invalid_duration_arguments(tmp_path):
    path = tmp_path / "tone.wav"
    write_wav(path)
    with pytest.raises(ValueError, match="must not be negative"):
        check_audio(path, duration_tolerance_seconds=-1)
    with pytest.raises(ValueError, match="must be positive"):
        check_audio(path, expected_duration_seconds=0)
