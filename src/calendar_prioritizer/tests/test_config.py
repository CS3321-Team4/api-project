from __future__ import annotations

from calendar_prioritizer.core.config import DEFAULT_GOOGLE_SCOPES, Settings


def test_google_scopes_accepts_comma_separated_env(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_SCOPES", "openid,email,profile,https://www.googleapis.com/auth/calendar.readonly")

    settings = Settings()

    assert settings.google_scopes == list(DEFAULT_GOOGLE_SCOPES)
