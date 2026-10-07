import importlib
from pathlib import Path

import pytest

import config


def test_defaults(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("YOUTUBE_CLIENT_SECRETS_FILE", raising=False)
    monkeypatch.delenv("YOUTUBE_TOKEN_FILE", raising=False)
    monkeypatch.delenv("TTS_VOICE", raising=False)

    importlib.reload(config)

    assert config.GEMINI_API_KEY == ""
    assert config.GEMINI_MODEL == "gemini-3.8-flash"
    assert config.YOUTUBE_API_KEY == ""
    assert config.YOUTUBE_CLIENT_SECRETS_FILE == Path("client_secrets.json")
    assert config.YOUTUBE_TOKEN_FILE == Path("token.json")
    assert config.TTS_VOICE == "hi-IN-MadhurNeural"


def test_environment_values(monkeypatch, tmp_path):
    client_file = tmp_path / "client.json"
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("YOUTUBE_API_KEY", "youtube-key")
    monkeypatch.setenv("YOUTUBE_CLIENT_SECRETS_FILE", str(client_file))
    monkeypatch.setenv("YOUTUBE_TOKEN_FILE", "test-token.json")
    monkeypatch.setenv("TTS_VOICE", "test-voice")

    importlib.reload(config)

    assert config.GEMINI_API_KEY == "test-key"
    assert config.GEMINI_MODEL == "test-model"
    assert config.YOUTUBE_API_KEY == "youtube-key"
    assert config.YOUTUBE_CLIENT_SECRETS_FILE == client_file
    assert config.YOUTUBE_TOKEN_FILE == Path("test-token.json")
    assert config.TTS_VOICE == "test-voice"


def test_validate_config_for_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    importlib.reload(config)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        config.validate_config(require_gemini=True)


def test_validate_config_for_youtube(tmp_path, monkeypatch):
    client_file = tmp_path / "client.json"
    monkeypatch.setenv("YOUTUBE_CLIENT_SECRETS_FILE", str(client_file))
    importlib.reload(config)

    with pytest.raises(RuntimeError, match="YOUTUBE_CLIENT_SECRETS_FILE"):
        config.validate_config(require_youtube=True)

    client_file.write_text("{}", encoding="utf-8")
    importlib.reload(config)
    config.validate_config(require_youtube=True)
