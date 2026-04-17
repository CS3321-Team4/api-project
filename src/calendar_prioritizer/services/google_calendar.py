from __future__ import annotations

from datetime import datetime, timezone

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from calendar_prioritizer.core.config import Settings
from calendar_prioritizer.models.oauth_session import OAuthSession
from calendar_prioritizer.services.google_oauth import build_credentials, persist_credentials


class GoogleCalendarService:
    def __init__(self, db: Session, settings: Settings, oauth_session: OAuthSession):
        self.db = db
        self.settings = settings
        self.oauth_session = oauth_session

    def list_calendars(
        self,
        *,
        max_results: int = 50,
        min_access_role: str | None = None,
        page_token: str | None = None,
    ) -> dict:
        query_params: dict[str, object] = {'maxResults': max_results}
        if min_access_role:
            query_params['minAccessRole'] = min_access_role
        if page_token:
            query_params['pageToken'] = page_token

        return self._execute(lambda service: service.calendarList().list(**query_params))

    def get_calendar(self, calendar_id: str) -> dict:
        return self._execute(
            lambda service: service.calendarList().get(calendarId=calendar_id)
        )

    def list_events(
        self,
        calendar_id: str,
        *,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 50,
        page_token: str | None = None,
        single_events: bool = True,
        order_by: str | None = None,
        query: str | None = None,
        show_deleted: bool = False,
    ) -> dict:
        query_params: dict[str, object] = {
            'calendarId': calendar_id,
            'maxResults': max_results,
            'singleEvents': single_events,
            'showDeleted': show_deleted,
        }
        if time_min:
            query_params['timeMin'] = _to_rfc3339(time_min)
        if time_max:
            query_params['timeMax'] = _to_rfc3339(time_max)
        if page_token:
            query_params['pageToken'] = page_token
        if order_by:
            query_params['orderBy'] = order_by
        if query:
            query_params['q'] = query

        return self._execute(lambda service: service.events().list(**query_params))

    def get_event(self, calendar_id: str, event_id: str) -> dict:
        return self._execute(
            lambda service: service.events().get(calendarId=calendar_id, eventId=event_id)
        )

    def update_event_color(self, calendar_id: str, event_id: str, *, color_id: str) -> dict:
        return self._execute(
            lambda service: service.events().patch(
                calendarId=calendar_id,
                eventId=event_id,
                body={'colorId': color_id},
            )
        )

    def _execute(self, request_builder) -> dict:
        credentials = build_credentials(self.oauth_session, self.settings)
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(GoogleAuthRequest())
                persist_credentials(self.db, self.oauth_session, credentials)
            except RefreshError as exc:
                raise ValueError(
                    'Your Google session has expired. Please sign in again.'
                ) from exc

        service = build('calendar', 'v3', credentials=credentials, cache_discovery=False)
        response = request_builder(service).execute()
        persist_credentials(self.db, self.oauth_session, credentials)
        return response



def _to_rfc3339(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
