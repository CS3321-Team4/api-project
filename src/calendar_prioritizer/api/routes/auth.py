from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from calendar_prioritizer.api.dependencies import require_google_config
from calendar_prioritizer.core.config import Settings
from calendar_prioritizer.db.session import get_db
from calendar_prioritizer.schemas.auth import AuthStatusResponse, GoogleAuthorizationUrlResponse, LogoutResponse
from calendar_prioritizer.services.google_oauth import (
    GoogleConfigurationError,
    create_authorization_url,
    delete_session,
    exchange_code_for_credentials,
    load_session,
    upsert_session_from_credentials,
)

logger = logging.getLogger(__name__)

GOOGLE_OAUTH_STATE_SESSION_KEY = "google_oauth_state"
GOOGLE_OAUTH_CODE_VERIFIER_SESSION_KEY = "google_oauth_code_verifier"
GOOGLE_SESSION_ID_SESSION_KEY = "google_session_id"

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/url", response_model=GoogleAuthorizationUrlResponse)
def get_google_authorization_url(
    request: Request,
    settings: Settings = Depends(require_google_config),
) -> GoogleAuthorizationUrlResponse:
    authorization_url, state, code_verifier = create_authorization_url(settings)
    request.session[GOOGLE_OAUTH_STATE_SESSION_KEY] = state
    request.session[GOOGLE_OAUTH_CODE_VERIFIER_SESSION_KEY] = code_verifier
    return GoogleAuthorizationUrlResponse(authorization_url=authorization_url)


@router.get("/google/login")
def google_login(
    request: Request,
    settings: Settings = Depends(require_google_config),
) -> RedirectResponse:
    authorization_url, state, code_verifier = create_authorization_url(settings)
    request.session[GOOGLE_OAUTH_STATE_SESSION_KEY] = state
    request.session[GOOGLE_OAUTH_CODE_VERIFIER_SESSION_KEY] = code_verifier
    return RedirectResponse(url=authorization_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/google/callback", response_class=HTMLResponse, response_model=None)
def google_callback(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(require_google_config),
) -> Response:
    error = request.query_params.get("error")
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth returned an error: {error}",
        )

    expected_state = request.session.get(GOOGLE_OAUTH_STATE_SESSION_KEY)
    received_state = request.query_params.get("state")
    if not expected_state or received_state != expected_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state. Start the sign-in flow again.",
        )

    code = request.query_params.get("code")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OAuth authorization code. Start the sign-in flow again.",
        )

    code_verifier = request.session.get(GOOGLE_OAUTH_CODE_VERIFIER_SESSION_KEY)
    if not code_verifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OAuth code verifier. Start the sign-in flow again.",
        )

    try:
        credentials = exchange_code_for_credentials(
            settings=settings,
            code=code,
            state=received_state,
            code_verifier=code_verifier,
        )
    except GoogleConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Google OAuth callback token exchange failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth callback could not be completed.",
        ) from exc

    existing_session_id = request.session.get(GOOGLE_SESSION_ID_SESSION_KEY)
    oauth_session = upsert_session_from_credentials(db, credentials, existing_session_id)
    request.session[GOOGLE_SESSION_ID_SESSION_KEY] = oauth_session.id
    request.session.pop(GOOGLE_OAUTH_STATE_SESSION_KEY, None)
    request.session.pop(GOOGLE_OAUTH_CODE_VERIFIER_SESSION_KEY, None)

    if settings.google_oauth_success_redirect:
        return RedirectResponse(url=settings.google_oauth_success_redirect, status_code=status.HTTP_302_FOUND)

    return HTMLResponse(
        content="""
        <html>
            <body>
                <h1>Google Calendar connected</h1>
                <p><a href="/">Open the priority dashboard</a> or continue testing the API in <code>/docs</code>.</p>
            </body>
        </html>
        """,
        status_code=status.HTTP_200_OK,
    )


@router.get("/me", response_model=AuthStatusResponse)
def get_auth_status(
    request: Request,
    db: Session = Depends(get_db),
) -> AuthStatusResponse:
    session_id = request.session.get(GOOGLE_SESSION_ID_SESSION_KEY)
    if not session_id:
        return AuthStatusResponse(is_authenticated=False)

    oauth_session = load_session(db, session_id)
    if oauth_session is None:
        request.session.pop(GOOGLE_SESSION_ID_SESSION_KEY, None)
        return AuthStatusResponse(is_authenticated=False)

    return AuthStatusResponse(
        is_authenticated=True,
        session_id=oauth_session.id,
        scopes=oauth_session.get_scopes(),
        granted_scopes=oauth_session.get_granted_scopes(),
        expires_at=oauth_session.expiry,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    db: Session = Depends(get_db),
) -> LogoutResponse:
    session_id = request.session.pop(GOOGLE_SESSION_ID_SESSION_KEY, None)
    request.session.pop(GOOGLE_OAUTH_STATE_SESSION_KEY, None)
    request.session.pop(GOOGLE_OAUTH_CODE_VERIFIER_SESSION_KEY, None)

    if session_id:
        delete_session(db, session_id)

    return LogoutResponse()
