from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.session import get_db
from app.models.oauth_session import OAuthSession
from app.services.google_calendar import GoogleCalendarService
from app.services.google_oauth import load_session



def get_settings_dependency(request: Request) -> Settings:
    return request.app.state.settings



def require_google_config(
    settings: Settings = Depends(get_settings_dependency),
) -> Settings:
    if settings.google_is_configured:
        return settings

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
    )



def get_current_oauth_session(
    request: Request,
    db: Session = Depends(get_db),
) -> OAuthSession:
    session_id = request.session.get("google_session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must sign in with Google before calling this endpoint.",
        )

    oauth_session = load_session(db, session_id)
    if oauth_session is None:
        request.session.pop("google_session_id", None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session is no longer available. Please sign in again.",
        )

    return oauth_session



def get_google_calendar_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(require_google_config),
    oauth_session: OAuthSession = Depends(get_current_oauth_session),
) -> GoogleCalendarService:
    return GoogleCalendarService(db=db, settings=settings, oauth_session=oauth_session)
