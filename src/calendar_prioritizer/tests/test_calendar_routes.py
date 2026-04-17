from __future__ import annotations

from calendar_prioritizer.api.dependencies import get_google_calendar_service


class FakeGoogleCalendarService:
    def list_calendars(self, **kwargs):
        return {
            'items': [
                {
                    'id': 'primary',
                    'summary': 'Personal',
                    'timeZone': 'America/Denver',
                    'accessRole': 'owner',
                    'primary': True,
                    'selected': True,
                }
            ],
            'nextPageToken': None,
        }

    def get_calendar(self, calendar_id: str):
        return {
            'id': calendar_id,
            'summary': 'Personal',
            'timeZone': 'America/Denver',
            'accessRole': 'owner',
            'primary': True,
            'selected': True,
        }

    def list_events(self, calendar_id: str, **kwargs):
        return {
            'timeZone': 'America/Denver',
            'items': [
                {
                    'id': 'event-1',
                    'status': 'confirmed',
                    'summary': 'Project meeting',
                    'htmlLink': 'https://calendar.google.com/event?eid=abc',
                    'start': {'dateTime': '2026-04-16T15:00:00-06:00', 'timeZone': 'America/Denver'},
                    'end': {'dateTime': '2026-04-16T16:00:00-06:00', 'timeZone': 'America/Denver'},
                    'organizer': {'email': 'owner@example.com'},
                    'creator': {'email': 'owner@example.com'},
                }
            ],
            'nextPageToken': 'next-page',
        }

    def get_event(self, calendar_id: str, event_id: str):
        color_id = '5'
        if event_id == 'unmapped-event':
            color_id = '1'

        return {
            'id': event_id,
            'status': 'confirmed',
            'summary': 'Project meeting',
            'colorId': color_id,
            'start': {'dateTime': '2026-04-16T15:00:00-06:00', 'timeZone': 'America/Denver'},
            'end': {'dateTime': '2026-04-16T16:00:00-06:00', 'timeZone': 'America/Denver'},
            'organizer': {'email': 'owner@example.com'},
            'creator': {'email': 'owner@example.com'},
        }

    def update_event_color(self, calendar_id: str, event_id: str, *, color_id: str):
        return {
            'id': event_id,
            'status': 'confirmed',
            'summary': 'Project meeting',
            'colorId': color_id,
            'start': {'dateTime': '2026-04-16T15:00:00-06:00', 'timeZone': 'America/Denver'},
            'end': {'dateTime': '2026-04-16T16:00:00-06:00', 'timeZone': 'America/Denver'},
            'organizer': {'email': 'owner@example.com'},
            'creator': {'email': 'owner@example.com'},
        }



def test_list_calendars_requires_auth(client) -> None:
    response = client.get('/api/calendars')

    assert response.status_code == 401
    assert response.json()['detail'] == 'You must sign in with Google before calling this endpoint.'



def test_list_calendars_returns_serialized_response(client) -> None:
    client.app.dependency_overrides[get_google_calendar_service] = lambda: FakeGoogleCalendarService()

    response = client.get('/api/calendars')

    assert response.status_code == 200
    assert response.json() == {
        'items': [
            {
                'id': 'primary',
                'summary': 'Personal',
                'description': None,
                'time_zone': 'America/Denver',
                'access_role': 'owner',
                'selected': True,
                'primary': True,
                'hidden': None,
                'background_color': None,
                'foreground_color': None,
                'html_link': None,
            }
        ],
        'next_page_token': None,
    }

    client.app.dependency_overrides.clear()



def test_list_events_returns_calendar_events(client) -> None:
    client.app.dependency_overrides[get_google_calendar_service] = lambda: FakeGoogleCalendarService()

    response = client.get('/api/calendars/primary/events')

    assert response.status_code == 200
    assert response.json()['calendar_id'] == 'primary'
    assert response.json()['time_zone'] == 'America/Denver'
    assert response.json()['next_page_token'] == 'next-page'
    assert response.json()['items'][0]['id'] == 'event-1'
    assert response.json()['items'][0]['organizer_email'] == 'owner@example.com'
    assert response.json()['items'][0]['color_id'] is None

    client.app.dependency_overrides.clear()



def test_list_events_validates_start_time_ordering(client) -> None:
    client.app.dependency_overrides[get_google_calendar_service] = lambda: FakeGoogleCalendarService()

    response = client.get('/api/calendars/primary/events?order_by=startTime&single_events=false')

    assert response.status_code == 422
    assert response.json()['detail'] == "single_events must be true when order_by is 'startTime'."

    client.app.dependency_overrides.clear()



def test_update_event_color_returns_updated_event(client) -> None:
    client.app.dependency_overrides[get_google_calendar_service] = lambda: FakeGoogleCalendarService()

    response = client.patch(
        '/api/calendars/primary/events/event-1',
        json={'color_id': '11'},
    )

    assert response.status_code == 200
    assert response.json()['id'] == 'event-1'
    assert response.json()['color_id'] == '11'

    client.app.dependency_overrides.clear()



def test_update_event_color_validates_request_body(client) -> None:
    client.app.dependency_overrides[get_google_calendar_service] = lambda: FakeGoogleCalendarService()

    response = client.patch(
        '/api/calendars/primary/events/event-1',
        json={'color_id': ''},
    )

    assert response.status_code == 422

    client.app.dependency_overrides.clear()



def test_update_event_priority_returns_mapped_priority(client) -> None:
    client.app.dependency_overrides[get_google_calendar_service] = lambda: FakeGoogleCalendarService()

    response = client.patch('/api/calendars/primary/events/event-1/priority/4')

    assert response.status_code == 200
    assert response.json() == {
        'calendar_id': 'primary',
        'event_id': 'event-1',
        'priority': 4,
        'color_id': '6',
    }

    client.app.dependency_overrides.clear()



def test_update_event_priority_validates_range(client) -> None:
    client.app.dependency_overrides[get_google_calendar_service] = lambda: FakeGoogleCalendarService()

    response = client.patch('/api/calendars/primary/events/event-1/priority/6')

    assert response.status_code == 422

    client.app.dependency_overrides.clear()



def test_get_event_priority_returns_mapped_priority(client) -> None:
    client.app.dependency_overrides[get_google_calendar_service] = lambda: FakeGoogleCalendarService()

    response = client.get('/api/calendars/primary/events/event-1/priority/')

    assert response.status_code == 200
    assert response.json() == {
        'calendar_id': 'primary',
        'event_id': 'event-1',
        'priority': 3,
        'color_id': '5',
    }

    client.app.dependency_overrides.clear()



def test_get_event_priority_returns_none_for_unmapped_color(client) -> None:
    client.app.dependency_overrides[get_google_calendar_service] = lambda: FakeGoogleCalendarService()

    response = client.get('/api/calendars/primary/events/unmapped-event/priority/')

    assert response.status_code == 200
    assert response.json() == {
        'calendar_id': 'primary',
        'event_id': 'unmapped-event',
        'priority': None,
        'color_id': '1',
    }

    client.app.dependency_overrides.clear()
