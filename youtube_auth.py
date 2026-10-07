from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import YOUTUBE_CLIENT_SECRETS_FILE, YOUTUBE_TOKEN_FILE, validate_config

SCOPES = (
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
)


def _load_credentials(token_file: Path) -> Credentials | None:
    if not token_file.exists():
        return None
    try:
        credentials = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    except (ValueError, OSError) as exc:
        raise RuntimeError(f"Invalid YouTube OAuth token file: {token_file}") from exc
    return credentials


def authenticate_youtube(
    *,
    client_secrets_file: str | Path = YOUTUBE_CLIENT_SECRETS_FILE,
    token_file: str | Path = YOUTUBE_TOKEN_FILE,
) -> Credentials:
    client_secrets = Path(client_secrets_file).expanduser()
    token_path = Path(token_file).expanduser()

    if not client_secrets.exists():
        raise RuntimeError(
            f"YouTube OAuth client secrets file does not exist: {client_secrets}"
        )

    credentials = _load_credentials(token_path)

    if credentials and credentials.valid:
        return credentials

    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception as exc:
            raise RuntimeError("YouTube OAuth token refresh failed") from exc
    else:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets),
                SCOPES,
            )
            credentials = flow.run_local_server(port=0)
        except Exception as exc:
            raise RuntimeError("YouTube OAuth authorization failed") from exc

    if not credentials or not credentials.valid:
        raise RuntimeError("YouTube OAuth did not return valid credentials")

    token_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        token_path.write_text(credentials.to_json(), encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Could not save YouTube OAuth token: {token_path}") from exc

    return credentials


def get_youtube_client(
    *,
    client_secrets_file: str | Path = YOUTUBE_CLIENT_SECRETS_FILE,
    token_file: str | Path = YOUTUBE_TOKEN_FILE,
):
    credentials = authenticate_youtube(
        client_secrets_file=client_secrets_file,
        token_file=token_file,
    )
    try:
        return build("youtube", "v3", credentials=credentials)
    except Exception as exc:
        raise RuntimeError("Could not create YouTube Data API client") from exc


def validate_youtube_oauth_files() -> None:
    validate_config(require_youtube=True)
    if YOUTUBE_TOKEN_FILE.exists():
        try:
            credentials = Credentials.from_authorized_user_file(
                str(YOUTUBE_TOKEN_FILE),
                SCOPES,
            )
        except (ValueError, OSError) as exc:
            raise RuntimeError(
                f"Invalid YouTube OAuth token file: {YOUTUBE_TOKEN_FILE}"
            ) from exc
        if not credentials.valid and not credentials.refresh_token:
            raise RuntimeError(
                f"YouTube OAuth token needs reauthorization: {YOUTUBE_TOKEN_FILE}"
            )
