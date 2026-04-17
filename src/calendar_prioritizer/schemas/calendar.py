from __future__ import annotations

from datetime import date as date_value, datetime

from pydantic import BaseModel, Field


class CalendarDetailResponse(BaseModel):
    id: str
    summary: str | None = None
    description: str | None = None
    time_zone: str | None = None
    access_role: str | None = None
    selected: bool | None = None
    primary: bool | None = None
    hidden: bool | None = None
    background_color: str | None = None
    foreground_color: str | None = None
    html_link: str | None = None


class CalendarListResponse(BaseModel):
    items: list[CalendarDetailResponse] = Field(default_factory=list)
    next_page_token: str | None = None


class EventDateTimeInfo(BaseModel):
    date: date_value | None = None
    date_time: datetime | None = None
    time_zone: str | None = None


class CalendarEventResponse(BaseModel):
    id: str
    status: str | None = None
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    html_link: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    start: EventDateTimeInfo | None = None
    end: EventDateTimeInfo | None = None
    recurring_event_id: str | None = None
    event_type: str | None = None
    organizer_email: str | None = None
    creator_email: str | None = None


class CalendarEventsResponse(BaseModel):
    calendar_id: str
    time_zone: str | None = None
    items: list[CalendarEventResponse] = Field(default_factory=list)
    next_page_token: str | None = None
