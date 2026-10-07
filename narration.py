from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import edge_tts

from config import TTS_VOICE

DEFAULT_VOICE = "hi-IN-MadhurNeural"
_TICKS_PER_SECOND = 10_000_000


@dataclass(frozen=True)
class WordTiming:
    text: str
    start_seconds: float
    duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "start_seconds": self.start_seconds,
            "duration_seconds": self.duration_seconds,
        }


def _validate_timing(timings: list[WordTiming]) -> None:
    previous_end = 0.0
    for timing in timings:
        if not timing.text.strip():
            raise RuntimeError("TTS returned an empty word timing")
        if timing.start_seconds < previous_end:
            raise RuntimeError("TTS word timings are not monotonic")
        if timing.duration_seconds <= 0:
            raise RuntimeError("TTS returned a non-positive word duration")
        previous_end = timing.start_seconds + timing.duration_seconds


def _write_timing(
    path: Path,
    *,
    text: str,
    timings: list[WordTiming],
) -> None:
    _validate_timing(timings)
    duration = (
        0.0
        if not timings
        else timings[-1].start_seconds + timings[-1].duration_seconds
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "text": text,
        "duration_seconds": round(duration, 6),
        "words": [timing.to_dict() for timing in timings],
    }
    try:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(f"Could not write narration timing: {path}") from exc


def synthesize_speech(
    text: str,
    output_path: str | Path,
    *,
    voice: str | None = None,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
    timing_path: str | Path | None = None,
) -> Path:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must not be empty")

    clean_text = text.strip()
    selected_voice = (voice or TTS_VOICE or DEFAULT_VOICE).strip()
    if not selected_voice:
        raise ValueError("voice must not be empty")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    async def save() -> None:
        if timing_path is None:
            communicate = edge_tts.Communicate(
                clean_text,
                selected_voice,
                rate=rate,
                volume=volume,
                pitch=pitch,
            )
            await communicate.save(str(path))
            return

        communicate = edge_tts.Communicate(
            clean_text,
            selected_voice,
            rate=rate,
            volume=volume,
            pitch=pitch,
            boundary="WordBoundary",
        )
        timings: list[WordTiming] = []
        with path.open("wb") as audio:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    timings.append(
                        WordTiming(
                            text=str(chunk["text"]),
                            start_seconds=round(
                                int(chunk["offset"]) / _TICKS_PER_SECOND,
                                6,
                            ),
                            duration_seconds=round(
                                int(chunk["duration"]) / _TICKS_PER_SECOND,
                                6,
                            ),
                        )
                    )

        if not timings:
            raise RuntimeError("TTS returned no word timing events")

        _write_timing(
            Path(timing_path),
            text=clean_text,
            timings=timings,
        )

    try:
        asyncio.run(save())
    except Exception as exc:
        raise RuntimeError(f"Speech synthesis failed: {exc}") from exc

    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("Speech synthesis produced no audio")

    if timing_path is not None:
        timing_file = Path(timing_path)
        if not timing_file.exists() or timing_file.stat().st_size == 0:
            raise RuntimeError("Speech synthesis produced no timing data")

    return path
