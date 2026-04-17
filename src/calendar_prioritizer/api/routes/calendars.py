from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from googleapiclient.errors import HttpError

from calendar_prioritizer.api.dependencies import get_google_calendar_service
from calendar_prioritizer.schemas.calendar import (
    CalendarDetailResponse,
    CalendarEventResponse,
    CalendarEventsResponse,
    CalendarListResponse,
    EventDateTimeInfo,
)
from calendar_prioritizer.services.google_calendar import GoogleCalendarService

router = APIRouter(prefix="/calendars", tags=["google-calendar"])


@router.get("", response_model=CalendarListResponse)
def list_calendars(
    max_results: int = Query(default=50, ge=1, le=250),
    min_access_role: Literal["freeBusyReader", "reader", "writer", "owner"] | None = None,
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
    except HttpError as exc:
        _raise_google_error(exc)

    return CalendarListResponse(
        items=[_serialize_calendar(item) for item in payload.get("items", [])],
        next_page_token=payload.get("nextPageToken"),
    )


@router.get("/{calendar_id}", response_model=CalendarDetailResponse)
def get_calendar(
    calendar_id: str,
    service: GoogleCalendarService = Depends(get_google_calendar_service),
) -> CalendarDetailResponse:
    try:
        payload = service.get_calendar(calendar_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except HttpError as exc:
        _raise_google_error(exc)

    return _serialize_calendar(payload)


@router.get("/{calendar_id}/events", response_model=CalendarEventsResponse)
def list_events(
    calendar_id: str,
    time_min: datetime | None = None,
    time_max: datetime | None = None,
    max_results: int = Query(default=50, ge=1, le=2500),
    page_token: str | None = None,
    single_events: bool = True,
    order_by: Literal["startTime", "updated"] | None = None,
    query: str | None = None,
    show_deleted: bool = False,
    service: GoogleCalendarService = Depends(get_google_calendar_service),
) -> CalendarEventsResponse:
    if order_by == "startTime" and not single_events:
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
    except HttpError as exc:
        _raise_google_error(exc)

    return CalendarEventsResponse(
        calendar_id=calendar_id,
        time_zone=payload.get("timeZone"),
        items=[_serialize_event(item) for item in payload.get("items", [])],
        next_page_token=payload.get("nextPageToken"),
    )


@router.get("/{calendar_id}/events/{event_id}", response_model=CalendarEventResponse)
def get_event(
    calendar_id: str,
    event_id: str,
    service: GoogleCalendarService = Depends(get_google_calendar_service),
) -> CalendarEventResponse:
    try:
        payload = service.get_event(calendar_id=calendar_id, event_id=event_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except HttpError as exc:
        _raise_google_error(exc)

    return _serialize_event(payload)



def _serialize_calendar(payload: dict) -> CalendarDetailResponse:
    return CalendarDetailResponse(
        id=payload["id"],
        summary=payload.get("summary"),
        description=payload.get("description"),
        time_zone=payload.get("timeZone"),
        access_role=payload.get("accessRole"),
        selected=payload.get("selected"),
        primary=payload.get("primary"),
        hidden=payload.get("hidden"),
        background_color=payload.get("backgroundColor"),
        foreground_color=payload.get("foregroundColor"),
        html_link=payload.get("htmlLink"),
    )



def _serialize_event(payload: dict) -> CalendarEventResponse:
    return CalendarEventResponse(
        id=payload["id"],
        status=payload.get("status"),
        summary=payload.get("summary"),
        description=payload.get("description"),
        location=payload.get("location"),
        html_link=payload.get("htmlLink"),
        created=payload.get("created"),
        updated=payload.get("updated"),
        start=_serialize_event_time(payload.get("start")),
        end=_serialize_event_time(payload.get("end")),
        recurring_event_id=payload.get("recurringEventId"),
        event_type=payload.get("eventType"),
        organizer_email=(payload.get("organizer") or {}).get("email"),
        creator_email=(payload.get("creator") or {}).get("email"),
    )



def _serialize_event_time(payload: dict | None) -> EventDateTimeInfo | None:
    if payload is None:
        return None

    return EventDateTimeInfo(
        date=payload.get("date"),
        date_time=payload.get("dateTime"),
        time_zone=payload.get("timeZone"),
    )



def _raise_google_error(exc: HttpError) -> None:
    reason = getattr(exc, "reason", None) or str(exc)
    raise HTTPException(status_code=exc.resp.status, detail=reason) from exc
