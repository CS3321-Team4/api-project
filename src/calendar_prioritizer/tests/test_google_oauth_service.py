from __future__ import annotations

import os
from types import SimpleNamespace

from calendar_prioritizer.core.config import Settings
from calendar_prioritizer.services import google_oauth


class DummyFlow:
    def __init__(self) -> None:
        self.credentials = SimpleNamespace(token="access-token")
        self.seen_relax_value: str | None = None

    def fetch_token(self, *, code: str) -> None:
        assert code == "fake-code"
        self.seen_relax_value = os.environ.get("OAUTHLIB_RELAX_TOKEN_SCOPE")



def test_exchange_code_for_credentials_relaxes_scope_check(monkeypatch) -> None:
    settings = Settings(
        google_client_id="test-client-id",
        google_client_secret="test-client-secret",
    )
    flow = DummyFlow()

    monkeypatch.delenv("OAUTHLIB_RELAX_TOKEN_SCOPE", raising=False)
    monkeypatch.setattr(google_oauth, "build_google_flow", lambda settings, state, code_verifier: flow)

    credentials = google_oauth.exchange_code_for_credentials(
        settings=settings,
        code="fake-code",
        state="test-state",
        code_verifier="test-code-verifier",
    )

    assert credentials is flow.credentials
    assert flow.seen_relax_value == "1"
    assert os.environ.get("OAUTHLIB_RELAX_TOKEN_SCOPE") is None


def test_sync_model_from_credentials_handles_missing_optional_attributes() -> None:
    oauth_session = google_oauth.OAuthSession(id="test-session")
    credentials = SimpleNamespace(
        token="access-token",
        refresh_token="refresh-token",
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["openid", "email"],
        granted_scopes=["openid", "email"],
        expiry=None,
    )

    google_oauth._sync_model_from_credentials(oauth_session, credentials)

    assert oauth_session.access_token == "access-token"
    assert oauth_session.refresh_token == "refresh-token"
    assert oauth_session.token_type is None
    assert oauth_session.id_token is None
