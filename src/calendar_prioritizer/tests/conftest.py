from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from calendar_prioritizer.core.config import Settings
from calendar_prioritizer.main import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    database_path = tmp_path / "test.db"
    return Settings(
        database_url=f"sqlite:///{database_path}",
        session_secret="test-session-secret",
        google_client_id="test-client-id",
        google_client_secret="test-client-secret",
        google_redirect_uri="http://testserver/api/auth/google/callback",
        google_oauth_success_redirect=None,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
