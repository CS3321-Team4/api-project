import pytest
from datetime import datetime, timezone
from calendar_prioritizer.services.google_calendar import _to_rfc3339


def test_to_rfc3339_naive_datetime():
    value = datetime(2026, 4, 21, 12, 30, 0)

    result = _to_rfc3339(value)

    assert result == "2026-04-21T12:30:00Z"


def test_to_rfc3339_timezone_aware_datetime():
    value = datetime(2026, 4, 21, 12, 30, 0, tzinfo=timezone.utc)

    result = _to_rfc3339(value)

    assert result == "2026-04-21T12:30:00Z"

def test_list_calendars_builds_query_params(monkeypatch):
    from calendar_prioritizer.services.google_calendar import GoogleCalendarService

    service = GoogleCalendarService(
        db=object(),
        settings=object(),
        oauth_session=object(),
    )

    captured = {}

    def fake_execute(request_builder):
        class FakeCalendarList:
            def list(self, **kwargs):
                captured["kwargs"] = kwargs
                return "request"

        class FakeService:
            def calendarList(self):
                return FakeCalendarList()

        request_builder(FakeService())
        return {"items": []}

    monkeypatch.setattr(service, "_execute", fake_execute)

    result = service.list_calendars(
        max_results=10,
        min_access_role="owner",
        page_token="next-page",
    )

    assert result == {"items": []}
    assert captured["kwargs"] == {
        "maxResults": 10,
        "minAccessRole": "owner",
        "pageToken": "next-page",
    }


def test_get_calendar_builds_request(monkeypatch):
    from calendar_prioritizer.services.google_calendar import GoogleCalendarService

    service = GoogleCalendarService(
        db=object(),
        settings=object(),
        oauth_session=object(),
    )

    captured = {}

    def fake_execute(request_builder):
        class FakeCalendarList:
            def get(self, **kwargs):
                captured["kwargs"] = kwargs
                return "request"

        class FakeService:
            def calendarList(self):
                return FakeCalendarList()

        request_builder(FakeService())
        return {"id": "primary"}

    monkeypatch.setattr(service, "_execute", fake_execute)

    result = service.get_calendar("primary")

    assert result == {"id": "primary"}
    assert captured["kwargs"] == {"calendarId": "primary"}

def test_list_events_builds_query_params(monkeypatch):
    from datetime import datetime
    from calendar_prioritizer.services.google_calendar import GoogleCalendarService

    service = GoogleCalendarService(
        db=object(),
        settings=object(),
        oauth_session=object(),
    )

    captured = {}

    def fake_execute(request_builder):
        class FakeEvents:
            def list(self, **kwargs):
                captured["kwargs"] = kwargs
                return "request"

        class FakeService:
            def events(self):
                return FakeEvents()

        request_builder(FakeService())
        return {"items": []}

    monkeypatch.setattr(service, "_execute", fake_execute)

    result = service.list_events(
        "primary",
        time_min=datetime(2026, 4, 21, 10, 0, 0),
        time_max=datetime(2026, 4, 22, 10, 0, 0),
        max_results=25,
        page_token="token123",
        single_events=False,
        order_by="startTime",
        query="meeting",
        show_deleted=True,
    )

    assert result == {"items": []}
    assert captured["kwargs"] == {
        "calendarId": "primary",
        "maxResults": 25,
        "singleEvents": False,
        "showDeleted": True,
        "timeMin": "2026-04-21T10:00:00Z",
        "timeMax": "2026-04-22T10:00:00Z",
        "pageToken": "token123",
        "orderBy": "startTime",
        "q": "meeting",
    }


def test_get_event_builds_request(monkeypatch):
    from calendar_prioritizer.services.google_calendar import GoogleCalendarService

    service = GoogleCalendarService(
        db=object(),
        settings=object(),
        oauth_session=object(),
    )

    captured = {}

    def fake_execute(request_builder):
        class FakeEvents:
            def get(self, **kwargs):
                captured["kwargs"] = kwargs
                return "request"

        class FakeService:
            def events(self):
                return FakeEvents()

        request_builder(FakeService())
        return {"id": "event1"}

    monkeypatch.setattr(service, "_execute", fake_execute)

    result = service.get_event("primary", "event1")

    assert result == {"id": "event1"}
    assert captured["kwargs"] == {
        "calendarId": "primary",
        "eventId": "event1",
    }

from types import SimpleNamespace
from google.auth.exceptions import RefreshError

def test_update_event_color_builds_patch_request(monkeypatch):
    from calendar_prioritizer.services.google_calendar import GoogleCalendarService

    service = GoogleCalendarService(
        db=object(),
        settings=object(),
        oauth_session=object(),
    )

    captured = {}

    def fake_execute(request_builder):
        class FakeEvents:
            def patch(self, **kwargs):
                captured["kwargs"] = kwargs
                return "request"

        class FakeService:
            def events(self):
                return FakeEvents()

        request_builder(FakeService())
        return {"id": "event1", "colorId": "5"}

    monkeypatch.setattr(service, "_execute", fake_execute)

    result = service.update_event_color("primary", "event1", color_id="5")

    assert result == {"id": "event1", "colorId": "5"}
    assert captured["kwargs"] == {
        "calendarId": "primary",
        "eventId": "event1",
        "body": {"colorId": "5"},
    }


def test_execute_returns_response_and_persists_credentials(monkeypatch):
    from calendar_prioritizer.services.google_calendar import GoogleCalendarService

    oauth_session = object()
    db = object()
    settings = object()

    credentials = SimpleNamespace(
        expired=False,
        refresh_token="refresh-token",
    )

    persisted = []

    def fake_build_credentials(session, settings_obj):
        assert session is oauth_session
        assert settings_obj is settings
        return credentials

    def fake_persist_credentials(db_obj, session, creds):
        persisted.append((db_obj, session, creds))

    class FakeRequest:
        def execute(self):
            return {"items": ["a", "b"]}

    class FakeService:
        pass

    def fake_build(api_name, version, credentials=None, cache_discovery=None):
        assert api_name == "calendar"
        assert version == "v3"
        assert credentials is credentials_obj
        assert cache_discovery is False
        return FakeService()

    credentials_obj = credentials

    monkeypatch.setattr(
        "calendar_prioritizer.services.google_calendar.build_credentials",
        fake_build_credentials,
    )
    monkeypatch.setattr(
        "calendar_prioritizer.services.google_calendar.persist_credentials",
        fake_persist_credentials,
    )
    monkeypatch.setattr(
        "calendar_prioritizer.services.google_calendar.build",
        fake_build,
    )

    service = GoogleCalendarService(
        db=db,
        settings=settings,
        oauth_session=oauth_session,
    )

    result = service._execute(lambda svc: FakeRequest())

    assert result == {"items": ["a", "b"]}
    assert persisted == [(db, oauth_session, credentials)]


def test_execute_refresh_error_raises_value_error(monkeypatch):
    from calendar_prioritizer.services.google_calendar import GoogleCalendarService

    oauth_session = object()
    db = object()
    settings = object()

    class FakeCredentials:
        expired = True
        refresh_token = "refresh-token"

        def refresh(self, request):
            raise RefreshError("expired")

    monkeypatch.setattr(
        "calendar_prioritizer.services.google_calendar.build_credentials",
        lambda session, settings_obj: FakeCredentials(),
    )

    service = GoogleCalendarService(
        db=db,
        settings=settings,
        oauth_session=oauth_session,
    )

    with pytest.raises(ValueError, match="Your Google session has expired"):
        service._execute(lambda svc: None)

def test_execute_refresh_success_persists_twice(monkeypatch):
    from calendar_prioritizer.services.google_calendar import GoogleCalendarService

    oauth_session = object()
    db = object()
    settings = object()

    refresh_called = []
    persisted = []

    class FakeCredentials:
        expired = True
        refresh_token = "refresh-token"

        def refresh(self, request):
            refresh_called.append(request)

    credentials = FakeCredentials()

    def fake_build_credentials(session, settings_obj):
        return credentials

    def fake_persist_credentials(db_obj, session, creds):
        persisted.append((db_obj, session, creds))

    class FakeRequest:
        def execute(self):
            return {"ok": True}

    class FakeService:
        pass

    def fake_build(*args, **kwargs):
        return FakeService()

    monkeypatch.setattr(
        "calendar_prioritizer.services.google_calendar.build_credentials",
        fake_build_credentials,
    )
    monkeypatch.setattr(
        "calendar_prioritizer.services.google_calendar.persist_credentials",
        fake_persist_credentials,
    )
    monkeypatch.setattr(
        "calendar_prioritizer.services.google_calendar.build",
        fake_build,
    )

    service = GoogleCalendarService(
        db=db,
        settings=settings,
        oauth_session=oauth_session,
    )

    result = service._execute(lambda svc: FakeRequest())

    assert result == {"ok": True}
    assert len(refresh_called) == 1
    assert len(persisted) == 2