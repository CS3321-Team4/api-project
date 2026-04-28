from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from googleapiclient.errors import HttpError

from calendar_prioritizer.api.dependencies import get_google_calendar_service
from calendar_prioritizer.schemas.calendar import (
    CalendarDetailResponse,
    CalendarEventResponse,
    CalendarEventsResponse,
    CalendarListResponse,
    EventColorUpdateRequest,
    EventDateTimeInfo,
    EventPriorityResponse,
)
from calendar_prioritizer.services.google_calendar import GoogleCalendarConnectionError, GoogleCalendarService
from calendar_prioritizer.services.priorities import get_color_id_for_priority, get_priority_for_color_id

router = APIRouter(prefix='/calendars', tags=['google-calendar'])


@router.get('', response_model=CalendarListResponse)
def list_calendars(
    max_results: int = Query(default=50, ge=1, le=250),
    min_access_role: Literal['freeBusyReader', 'reader', 'writer', 'owner'] | None = None,
    page_token: str | None = None,
    service: GoogleCalendarService = Depends(get_google_calendar_service),
) -> CalendarListResponse:
    try:
        payload = service.list_calendars(
            max_results=max_results,
            min_access_role=min_access_role,
            page_token=page_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except GoogleCalendarConnectionError as exc:
        _raise_google_connection_error(exc)
    except HttpError as exc:
        _raise_google_error(exc)

    return CalendarListResponse(
        items=[_serialize_calendar(item) for item in payload.get('items', [])],
        next_page_token=payload.get('nextPageToken'),
    )


@router.get('/{calendar_id}', response_model=CalendarDetailResponse)
def get_calendar(
    calendar_id: str,
    service: GoogleCalendarService = Depends(get_google_calendar_service),
) -> CalendarDetailResponse:
    try:
        payload = service.get_calendar(calendar_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except GoogleCalendarConnectionError as exc:
        _raise_google_connection_error(exc)
    except HttpError as exc:
        _raise_google_error(exc)

    return _serialize_calendar(payload)


@router.get('/{calendar_id}/events', response_model=CalendarEventsResponse)
def list_events(
    calendar_id: str,
    time_min: datetime | None = None,
    time_max: datetime | None = None,
    max_results: int = Query(default=50, ge=1, le=2500),
    page_token: str | None = None,
    single_events: bool = True,
    order_by: Literal['startTime', 'updated'] | None = None,
    query: str | None = None,
    show_deleted: bool = False,
    service: GoogleCalendarService = Depends(get_google_calendar_service),
) -> CalendarEventsResponse:
    if order_by == 'startTime' and not single_events:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="single_events must be true when order_by is 'startTime'.",
        )

    try:
        payload = service.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
            page_token=page_token,
            single_events=single_events,
            order_by=order_by,
            query=query,
            show_deleted=show_deleted,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except GoogleCalendarConnectionError as exc:
        _raise_google_connection_error(exc)
    except HttpError as exc:
        _raise_google_error(exc)

    return CalendarEventsResponse(
        calendar_id=calendar_id,
        time_zone=payload.get('timeZone'),
        items=[_serialize_event(item) for item in payload.get('items', [])],
        next_page_token=payload.get('nextPageToken'),
    )


@router.get('/{calendar_id}/events/{event_id}', response_model=CalendarEventResponse)
def get_event(
    calendar_id: str,
    event_id: str,
    service: GoogleCalendarService = Depends(get_google_calendar_service),
) -> CalendarEventResponse:
    try:
        payload = service.get_event(calendar_id=calendar_id, event_id=event_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except GoogleCalendarConnectionError as exc:
        _raise_google_connection_error(exc)
    except HttpError as exc:
        _raise_google_error(exc)

    return _serialize_event(payload)


@router.patch('/{calendar_id}/events/{event_id}', response_model=CalendarEventResponse)
def update_event_color(
    calendar_id: str,
    event_id: str,
    payload: EventColorUpdateRequest,
    service: GoogleCalendarService = Depends(get_google_calendar_service),
) -> CalendarEventResponse:
    try:
        response = service.update_event_color(
            calendar_id=calendar_id,
            event_id=event_id,
            color_id=payload.color_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except GoogleCalendarConnectionError as exc:
        _raise_google_connection_error(exc)
    except HttpError as exc:
        _raise_google_error(exc)

    return _serialize_event(response)


@router.patch('/{calendar_id}/events/{event_id}/priority/{priority_id}', response_model=EventPriorityResponse)
def update_event_priority(
    calendar_id: str,
    event_id: str,
    priority_id: int = Path(ge=1, le=5),
    service: GoogleCalendarService = Depends(get_google_calendar_service),
) -> EventPriorityResponse:
    try:
        color_id = get_color_id_for_priority(priority_id)
        response = service.update_event_color(
            calendar_id=calendar_id,
            event_id=event_id,
            color_id=color_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except GoogleCalendarConnectionError as exc:
        _raise_google_connection_error(exc)
    except HttpError as exc:
        _raise_google_error(exc)

    return _serialize_priority(
        calendar_id=calendar_id,
        event_id=event_id,
        color_id=response.get('colorId'),
    )


@router.get('/{calendar_id}/events/{event_id}/priority/', response_model=EventPriorityResponse)
def get_event_priority(
    calendar_id: str,
    event_id: str,
    service: GoogleCalendarService = Depends(get_google_calendar_service),
) -> EventPriorityResponse:
    try:
        response = service.get_event(calendar_id=calendar_id, event_id=event_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except GoogleCalendarConnectionError as exc:
        _raise_google_connection_error(exc)
    except HttpError as exc:
        _raise_google_error(exc)

    return _serialize_priority(
        calendar_id=calendar_id,
        event_id=event_id,
        color_id=response.get('colorId'),
    )



def _serialize_calendar(payload: dict) -> CalendarDetailResponse:
    return CalendarDetailResponse(
        id=payload['id'],
        summary=payload.get('summary'),
        description=payload.get('description'),
        time_zone=payload.get('timeZone'),
        access_role=payload.get('accessRole'),
        selected=payload.get('selected'),
        primary=payload.get('primary'),
        hidden=payload.get('hidden'),
        background_color=payload.get('backgroundColor'),
        foreground_color=payload.get('foregroundColor'),
        html_link=payload.get('htmlLink'),
    )



def _serialize_event(payload: dict) -> CalendarEventResponse:
    return CalendarEventResponse(
        id=payload['id'],
        status=payload.get('status'),
        summary=payload.get('summary'),
        description=payload.get('description'),
        location=payload.get('location'),
        color_id=payload.get('colorId'),
        html_link=payload.get('htmlLink'),
        created=payload.get('created'),
        updated=payload.get('updated'),
        start=_serialize_event_time(payload.get('start')),
        end=_serialize_event_time(payload.get('end')),
        recurring_event_id=payload.get('recurringEventId'),
        event_type=payload.get('eventType'),
        organizer_email=(payload.get('organizer') or {}).get('email'),
        creator_email=(payload.get('creator') or {}).get('email'),
    )



def _serialize_priority(*, calendar_id: str, event_id: str, color_id: str | None) -> EventPriorityResponse:
    return EventPriorityResponse(
        calendar_id=calendar_id,
        event_id=event_id,
        priority=get_priority_for_color_id(color_id),
        color_id=color_id,
    )



def _serialize_event_time(payload: dict | None) -> EventDateTimeInfo | None:
    if payload is None:
        return None

    return EventDateTimeInfo(
        date=payload.get('date'),
        date_time=payload.get('dateTime'),
        time_zone=payload.get('timeZone'),
    )



def _raise_google_error(exc: HttpError) -> None:
    reason = getattr(exc, 'reason', None) or str(exc)
    raise HTTPException(status_code=exc.resp.status, detail=reason) from exc


def _raise_google_connection_error(exc: GoogleCalendarConnectionError) -> None:
    raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
