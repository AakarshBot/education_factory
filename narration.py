from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts

from config import TTS_VOICE

DEFAULT_VOICE = "hi-IN-MadhurNeural"


def synthesize_speech(
    text: str,
    output_path: str | Path,
    *,
    voice: str | None = None,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
) -> Path:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must not be empty")

    selected_voice = (voice or TTS_VOICE or DEFAULT_VOICE).strip()
    if not selected_voice:
        raise ValueError("voice must not be empty")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    async def save() -> None:
        communicate = edge_tts.Communicate(
            text.strip(),
            selected_voice,
            rate=rate,
            volume=volume,
            pitch=pitch,
        )
        await communicate.save(str(path))

    try:
        asyncio.run(save())
    except Exception as exc:
        raise RuntimeError(f"Speech synthesis failed: {exc}") from exc

    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("Speech synthesis produced no audio")

    return path
