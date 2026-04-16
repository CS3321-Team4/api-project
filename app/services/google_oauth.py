from __future__ import annotations

import json
from datetime import timezone
from uuid import uuid4

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.oauth_session import OAuthSession


class GoogleConfigurationError(RuntimeError):
    pass



def ensure_google_configured(settings: Settings) -> None:
    if settings.google_is_configured:
        return

    raise GoogleConfigurationError(
        "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
    )



def build_google_flow(settings: Settings, state: str | None = None) -> Flow:
    ensure_google_configured(settings)

    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": settings.google_auth_uri,
            "token_uri": settings.google_token_uri,
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }

    flow = Flow.from_client_config(client_config, scopes=settings.google_scopes, state=state)
    flow.redirect_uri = settings.google_redirect_uri
    return flow



def create_authorization_url(settings: Settings) -> tuple[str, str]:
    flow = build_google_flow(settings)
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt=settings.google_prompt,
    )
    return authorization_url, state



def exchange_code_for_credentials(
    settings: Settings,
    authorization_response: str,
    state: str,
) -> Credentials:
    flow = build_google_flow(settings, state=state)
    flow.fetch_token(authorization_response=authorization_response)
    return flow.credentials



def load_session(db: Session, session_id: str) -> OAuthSession | None:
    return db.get(OAuthSession, session_id)



def delete_session(db: Session, session_id: str) -> None:
    oauth_session = load_session(db, session_id)
    if oauth_session is None:
        return

    db.delete(oauth_session)
    db.commit()



def upsert_session_from_credentials(
    db: Session,
    credentials: Credentials,
    session_id: str | None = None,
) -> OAuthSession:
    oauth_session = load_session(db, session_id) if session_id else None
    if oauth_session is None:
        oauth_session = OAuthSession(id=session_id or str(uuid4()))

    _sync_model_from_credentials(oauth_session, credentials)
    db.add(oauth_session)
    db.commit()
    db.refresh(oauth_session)
    return oauth_session



def build_credentials(oauth_session: OAuthSession, settings: Settings) -> Credentials:
    ensure_google_configured(settings)

    return Credentials(
        token=oauth_session.access_token,
        refresh_token=oauth_session.refresh_token,
        token_uri=oauth_session.token_uri,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=oauth_session.get_granted_scopes(),
        expiry=oauth_session.expiry,
        id_token=oauth_session.id_token,
    )



def persist_credentials(
    db: Session,
    oauth_session: OAuthSession,
    credentials: Credentials,
) -> OAuthSession:
    _sync_model_from_credentials(oauth_session, credentials)
    db.add(oauth_session)
    db.commit()
    db.refresh(oauth_session)
    return oauth_session



def _sync_model_from_credentials(oauth_session: OAuthSession, credentials: Credentials) -> None:
    scopes = list(credentials.scopes or [])
    granted_scopes = list(getattr(credentials, "granted_scopes", None) or scopes)
    expiry = credentials.expiry
    if expiry is not None and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    oauth_session.access_token = credentials.token or ""
    oauth_session.refresh_token = credentials.refresh_token
    oauth_session.token_uri = credentials.token_uri or "https://oauth2.googleapis.com/token"
    oauth_session.scopes = json.dumps(scopes)
    oauth_session.granted_scopes = json.dumps(granted_scopes)
    oauth_session.token_type = credentials.token_type
    oauth_session.expiry = expiry
    oauth_session.id_token = credentials.id_token
