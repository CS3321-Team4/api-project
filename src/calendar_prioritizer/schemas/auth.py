from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GoogleAuthorizationUrlResponse(BaseModel):
    authorization_url: str


class AuthStatusResponse(BaseModel):
    is_authenticated: bool
    session_id: str | None = None
    scopes: list[str] = Field(default_factory=list)
    granted_scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None


class LogoutResponse(BaseModel):
    logged_out: bool = True
