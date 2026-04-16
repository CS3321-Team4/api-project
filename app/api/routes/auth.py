from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.api.dependencies import require_google_config
from app.core.config import Settings
from app.db.session import get_db
from app.schemas.auth import AuthStatusResponse, GoogleAuthorizationUrlResponse, LogoutResponse
from app.services.google_oauth import (
    GoogleConfigurationError,
    create_authorization_url,
    delete_session,
    exchange_code_for_credentials,
    load_session,
    upsert_session_from_credentials,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/url", response_model=GoogleAuthorizationUrlResponse)
def get_google_authorization_url(
    request: Request,
    settings: Settings = Depends(require_google_config),
) -> GoogleAuthorizationUrlResponse:
    authorization_url, state = create_authorization_url(settings)
    request.session["google_oauth_state"] = state
    return GoogleAuthorizationUrlResponse(authorization_url=authorization_url)


@router.get("/google/login")
def google_login(
    request: Request,
    settings: Settings = Depends(require_google_config),
) -> RedirectResponse:
    authorization_url, state = create_authorization_url(settings)
    request.session["google_oauth_state"] = state
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

    expected_state = request.session.get("google_oauth_state")
    received_state = request.query_params.get("state")
    if not expected_state or received_state != expected_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state. Start the sign-in flow again.",
        )

    try:
        credentials = exchange_code_for_credentials(
            settings=settings,
            authorization_response=str(request.url),
            state=received_state,
        )
    except GoogleConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth callback could not be completed.",
        ) from exc

    existing_session_id = request.session.get("google_session_id")
    oauth_session = upsert_session_from_credentials(db, credentials, existing_session_id)
    request.session["google_session_id"] = oauth_session.id
    request.session.pop("google_oauth_state", None)

    if settings.google_oauth_success_redirect:
        return RedirectResponse(url=settings.google_oauth_success_redirect, status_code=status.HTTP_302_FOUND)

    return HTMLResponse(
        content="""
        <html>
            <body>
                <h1>Google Calendar connected</h1>
                <p>You can return to your app or continue testing the API in <code>/docs</code>.</p>
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
    session_id = request.session.get("google_session_id")
    if not session_id:
        return AuthStatusResponse(is_authenticated=False)

    oauth_session = load_session(db, session_id)
    if oauth_session is None:
        request.session.pop("google_session_id", None)
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
    session_id = request.session.pop("google_session_id", None)
    request.session.pop("google_oauth_state", None)

    if session_id:
        delete_session(db, session_id)

    return LogoutResponse()
