import json

import pytest

import youtube_auth


class FakeCredentials:
    def __init__(self, *, valid=True, expired=False, refresh_token=True):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.refreshed = False

    def refresh(self, request):
        self.refreshed = True
        self.valid = True

    def to_json(self):
        return json.dumps({"token": "fake"})


def test_authenticate_uses_existing_valid_token(monkeypatch, tmp_path):
    client = tmp_path / "client.json"
    token = tmp_path / "token.json"
    client.write_text("client", encoding="utf-8")
    token.write_text("token", encoding="utf-8")
    credentials = FakeCredentials()
    monkeypatch.setattr(youtube_auth, "_load_credentials", lambda path: credentials)
    result = youtube_auth.authenticate_youtube(
        client_secrets_file=client,
        token_file=token,
    )
    assert result is credentials
    assert not credentials.refreshed


def test_authenticate_refreshes_expired_token(monkeypatch, tmp_path):
    client = tmp_path / "client.json"
    token = tmp_path / "token.json"
    client.write_text("client", encoding="utf-8")
    credentials = FakeCredentials(valid=False, expired=True, refresh_token=True)
    monkeypatch.setattr(youtube_auth, "_load_credentials", lambda path: credentials)
    result = youtube_auth.authenticate_youtube(
        client_secrets_file=client,
        token_file=token,
    )
    assert result.valid
    assert credentials.refreshed
    assert token.exists()


def test_authenticate_runs_browser_flow_without_existing_token(monkeypatch, tmp_path):
    client = tmp_path / "client.json"
    token = tmp_path / "token.json"
    client.write_text("client", encoding="utf-8")

    class FakeFlow:
        def run_local_server(self, port):
            return FakeCredentials()

    monkeypatch.setattr(
        youtube_auth.InstalledAppFlow,
        "from_client_secrets_file",
        lambda path, scopes: FakeFlow(),
    )
    result = youtube_auth.authenticate_youtube(
        client_secrets_file=client,
        token_file=token,
    )
    assert result.valid
    assert token.exists()


def test_authenticate_rejects_missing_client_file(tmp_path):
    with pytest.raises(RuntimeError, match="client secrets file does not exist"):
        youtube_auth.authenticate_youtube(
            client_secrets_file=tmp_path / "missing.json",
            token_file=tmp_path / "token.json",
        )


def test_authenticate_fails_closed_when_refresh_fails(monkeypatch, tmp_path):
    client = tmp_path / "client.json"
    token = tmp_path / "token.json"
    client.write_text("client", encoding="utf-8")

    class BadCredentials(FakeCredentials):
        def refresh(self, request):
            raise RuntimeError("refresh failed")

    monkeypatch.setattr(
        youtube_auth,
        "_load_credentials",
        lambda path: BadCredentials(valid=False, expired=True, refresh_token=True),
    )
    with pytest.raises(RuntimeError, match="token refresh failed"):
        youtube_auth.authenticate_youtube(
            client_secrets_file=client,
            token_file=token,
        )
