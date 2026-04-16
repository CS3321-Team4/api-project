from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace



def test_google_login_redirects_to_google(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.auth.create_authorization_url",
        lambda settings: ("https://accounts.google.com/o/oauth2/auth?state=test-state", "test-state"),
    )

    response = client.get("/api/auth/google/login", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://accounts.google.com/o/oauth2/auth?state=test-state"
    assert "calendar_priority_session=" in response.headers["set-cookie"]



def test_google_callback_creates_session(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.auth.create_authorization_url",
        lambda settings: ("https://accounts.google.com/o/oauth2/auth?state=test-state", "test-state"),
    )

    credentials = SimpleNamespace(
        token="access-token",
        refresh_token="refresh-token",
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["openid", "email", "profile", "https://www.googleapis.com/auth/calendar.readonly"],
        granted_scopes=["openid", "email", "profile", "https://www.googleapis.com/auth/calendar.readonly"],
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        id_token=None,
        token_type="Bearer",
    )
    monkeypatch.setattr(
        "app.api.routes.auth.exchange_code_for_credentials",
        lambda settings, authorization_response, state: credentials,
    )

    client.get("/api/auth/google/url")
    callback_response = client.get("/api/auth/google/callback?state=test-state&code=fake-code")
    status_response = client.get("/api/auth/me")

    assert callback_response.status_code == 200
    assert "Google Calendar connected" in callback_response.text
    assert status_response.status_code == 200
    assert status_response.json()["is_authenticated"] is True
    assert status_response.json()["scopes"] == credentials.scopes



def test_logout_clears_google_session(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.auth.create_authorization_url",
        lambda settings: ("https://accounts.google.com/o/oauth2/auth?state=test-state", "test-state"),
    )

    credentials = SimpleNamespace(
        token="access-token",
        refresh_token="refresh-token",
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        granted_scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        id_token=None,
        token_type="Bearer",
    )
    monkeypatch.setattr(
        "app.api.routes.auth.exchange_code_for_credentials",
        lambda settings, authorization_response, state: credentials,
    )

    client.get("/api/auth/google/url")
    client.get("/api/auth/google/callback?state=test-state&code=fake-code")

    logout_response = client.post("/api/auth/logout")
    status_response = client.get("/api/auth/me")

    assert logout_response.status_code == 200
    assert logout_response.json() == {"logged_out": True}
    assert status_response.json() == {
        "is_authenticated": False,
        "session_id": None,
        "scopes": [],
        "granted_scopes": [],
        "expires_at": None,
    }
