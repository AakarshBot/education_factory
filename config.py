from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
YOUTUBE_CLIENT_SECRETS_FILE = Path(
    os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
).expanduser()
YOUTUBE_TOKEN_FILE = Path(
    os.getenv("YOUTUBE_TOKEN_FILE", "token.json")
).expanduser()

TTS_VOICE = os.getenv("TTS_VOICE", "hi-IN-MadhurNeural").strip()


def validate_config(
    *,
    require_gemini: bool = False,
    require_youtube: bool = False,
    require_youtube_api: bool = False,
) -> None:
    missing = []

    if require_gemini and not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")

    if require_youtube_api and not YOUTUBE_API_KEY:
        missing.append("YOUTUBE_API_KEY")

    if require_youtube and not YOUTUBE_CLIENT_SECRETS_FILE.exists():
        missing.append(f"YOUTUBE_CLIENT_SECRETS_FILE ({YOUTUBE_CLIENT_SECRETS_FILE})")

    if missing:
        raise RuntimeError("Missing required configuration: " + ", ".join(missing))
