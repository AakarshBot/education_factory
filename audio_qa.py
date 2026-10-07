from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioQAResult:
    duration_seconds: float
    sample_rate: int
    channels: int
    mean_volume_db: float
    max_volume_db: float


def _run(command: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise RuntimeError(f"Could not run media tool: {command[0]}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Media tool failed ({command[0]}): {detail[:500]}")
    return result.stdout + result.stderr


def _probe(path: Path) -> tuple[float, int, int]:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "a:0",
                "-show_entries", "stream=codec_type,sample_rate,channels",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1", str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError("Could not run ffprobe") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"ffprobe failed: {detail[:500]}")
    values = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    try:
        duration = float(values["duration"])
        sample_rate = int(values["sample_rate"])
        channels = int(values["channels"])
    except (KeyError, ValueError) as exc:
        raise RuntimeError("ffprobe returned incomplete audio metadata") from exc
    if duration <= 0 or sample_rate <= 0 or channels <= 0:
        raise RuntimeError("audio stream metadata is invalid")
    return duration, sample_rate, channels


def _volume_levels(path: Path) -> tuple[float, float]:
    output = _run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-af", "volumedetect", "-f", "null", "-",
    ])
    mean_match = re.search(r"mean_volume:s*(-?d+(?:.d+)?)s*dB", output)
    max_match = re.search(r"max_volume:s*(-?d+(?:.d+)?)s*dB", output)
    if not mean_match or not max_match:
        raise RuntimeError("ffmpeg returned incomplete volume analysis")
    return float(mean_match.group(1)), float(max_match.group(1))


def check_audio(
    path: str | Path,
    *,
    expected_duration_seconds: float | None = None,
    duration_tolerance_seconds: float = 1.0,
    min_duration_seconds: float = 0.1,
    silence_threshold_db: float = -50.0,
) -> AudioQAResult:
    audio_path = Path(path)
    if not audio_path.exists():
        raise RuntimeError(f"audio file does not exist: {audio_path}")
    if audio_path.stat().st_size == 0:
        raise RuntimeError(f"audio file is empty: {audio_path}")
    if duration_tolerance_seconds < 0:
        raise ValueError("duration_tolerance_seconds must not be negative")
    if min_duration_seconds < 0:
        raise ValueError("min_duration_seconds must not be negative")
    duration, sample_rate, channels = _probe(audio_path)
    if duration < min_duration_seconds:
        raise RuntimeError(f"audio is too short: {duration:.3f}s")
    mean_volume, max_volume = _volume_levels(audio_path)
    if max_volume <= silence_threshold_db:
        raise RuntimeError("audio appears to contain silence only")
    if expected_duration_seconds is not None:
        if expected_duration_seconds <= 0:
            raise ValueError("expected_duration_seconds must be positive")
        if abs(duration - expected_duration_seconds) > duration_tolerance_seconds:
            raise RuntimeError(
                f"audio duration mismatch: audio={duration:.3f}s expected={expected_duration_seconds:.3f}s"
            )
    return AudioQAResult(
        duration_seconds=round(duration, 6),
        sample_rate=sample_rate,
        channels=channels,
        mean_volume_db=round(mean_volume, 2),
        max_volume_db=round(max_volume, 2),
    )
