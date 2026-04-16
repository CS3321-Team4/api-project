from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OAuthSession(Base):
    __tablename__ = "oauth_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_uri: Mapped[str] = mapped_column(String(255))
    scopes: Mapped[str] = mapped_column(Text)
    granted_scopes: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    id_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
    )

    def get_scopes(self) -> list[str]:
        return _parse_scopes(self.scopes)

    def get_granted_scopes(self) -> list[str]:
        return _parse_scopes(self.granted_scopes) or self.get_scopes()



def _parse_scopes(serialized_scopes: str | None) -> list[str]:
    if not serialized_scopes:
        return []

    try:
        data = json.loads(serialized_scopes)
    except json.JSONDecodeError:
        return []

    if isinstance(data, list):
        return [str(scope) for scope in data]

    return []
