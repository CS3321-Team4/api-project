from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEFAULT_GOOGLE_SCOPES = (
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/calendar.readonly",
)


class Settings(BaseSettings):
    app_name: str = "Calendar Priority API"
    api_v1_prefix: str = "/api"
    database_url: str = "sqlite:///./app.db"
    session_secret: str = "change-me-in-production"
    session_cookie_name: str = "calendar_priority_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 30
    session_cookie_same_site: str = "lax"
    session_cookie_https_only: bool = False
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    google_oauth_success_redirect: str | None = None
    google_auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    google_token_uri: str = "https://oauth2.googleapis.com/token"
    google_scopes: Annotated[list[str], NoDecode] = Field(default_factory=lambda: list(DEFAULT_GOOGLE_SCOPES))
    google_prompt: str = "consent"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("google_scopes", mode="before")
    @classmethod
    def parse_google_scopes(cls, value: object) -> list[str]:
        if value is None or value == "":
            return list(DEFAULT_GOOGLE_SCOPES)
        if isinstance(value, str):
            return [scope.strip() for scope in value.split(",") if scope.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(scope).strip() for scope in value if str(scope).strip()]
        raise TypeError("GOOGLE_SCOPES must be a comma-separated string or list of scopes.")

    @property
    def google_is_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()

