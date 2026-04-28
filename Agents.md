# Agents Guide

## Purpose

This project started with a broad "Calendar Priority API" vision in [OLD_README.md](/c:/Users/kason/OneDrive/Desktop/ISU/CS3321/Team4-Project/api-project/OLD_README.md) and has since implemented a narrower but solid backend foundation described in [README.md](/c:/Users/kason/OneDrive/Desktop/ISU/CS3321/Team4-Project/api-project/README.md).

Future agents should preserve the current `src/calendar_prioritizer` architecture and build the remaining prioritization features on top of it instead of rewriting the project to match the older `app/` example structure.

## Current Project Structure

Keep using this package layout:

```text
src/calendar_prioritizer/
├── api/
│   ├── dependencies.py
│   ├── router.py
│   └── routes/
├── core/
├── db/
├── models/
├── schemas/
├── services/
├── tests/
└── main.py
```

Prefer adding new code to the existing layers:

- `api/routes`: HTTP endpoints only
- `api/dependencies`: dependency wiring and auth/session access
- `schemas`: request/response models
- `services`: Google Calendar logic, priority logic, orchestration
- `models`: SQLAlchemy persistence models
- `db`: engine/session/base setup
- `tests`: route and service coverage

Do not introduce a second application layout such as `app/` unless the team explicitly requests a full migration.

## Implemented From The Old README

These old-readme goals are already implemented in the current project:

- FastAPI backend exists and is running through `src/calendar_prioritizer/main.py`
- REST API endpoints exist
- Google Calendar integration exists
- Request/response validation exists through Pydantic models
- Secure configuration exists through environment variables
- Backend persistence exists, but currently only for OAuth sessions
- Automated tests exist with `pytest`
- Docker support exists with `Dockerfile` and `docker-compose.yml`

Also implemented beyond the old README's original detail:

- Google OAuth 2.0 sign-in flow
- Signed session-cookie auth
- User-scoped calendar listing and event retrieval
- Server-side token persistence and refresh handling

## Not Yet Implemented From The Old README

These are the main product features still missing relative to the original project vision:

- Assign a priority value to a calendar event
- Configurable priority scale such as `1..N`
- Map priority values to colors
- Persist event priority assignments in the backend
- Return event data enriched with priority/color metadata
- Old-readme event endpoints like a project-level `GET /events`, `GET /events/{event_id}`, and priority update endpoint
- Priority-focused tests for validation, color mapping, and persistence
- CI/CD workflows with GitHub Actions
- Deployment setup/documentation beyond local Docker usage

These "future improvements" from the old README are also not implemented:

- Frontend dashboard
- Multi-user product auth beyond Google session sign-in
- Custom color palettes
- Writing color metadata back to Google Calendar
- Analytics over time
- Recurring-event-specific priority handling

## Build Next

When extending the project, prioritize this sequence:

1. Add a persistence model for event priorities.
2. Add schemas for priority update requests and enriched event responses.
3. Add a priority/color mapping service.
4. Extend calendar event responses to include stored priority metadata.
5. Add endpoints for reading and updating event priority.
6. Add tests for the new model, service, and API routes.
7. Update `README.md` to reflect the new implemented surface area.

## Recommended Feature Shape

Implement missing functionality in a way that fits the current architecture:

- Keep Google calendar retrieval in `services/google_calendar.py` or a closely related service.
- Add a dedicated model for persisted event priorities rather than overloading `OAuthSession`.
- Use a stable event identity such as `calendar_id + event_id` for persistence.
- Keep OAuth/session behavior separate from prioritization behavior.
- Prefer composing enriched event responses server-side rather than mutating raw Google payloads everywhere.

Suggested additions:

- `models/event_priority.py`
- `schemas/priority.py`
- `services/priorities.py`
- `api/routes/priorities.py` or extend `api/routes/calendars.py` carefully
- tests covering both service logic and route behavior

## Guardrails For Future Agents

- Preserve the `src/calendar_prioritizer` package layout.
- Keep route handlers thin; business rules belong in services.
- Add persistence through SQLAlchemy models and the existing DB session pattern.
- Keep Pydantic schemas as the public contract for new endpoints.
- Avoid hard-coding secrets or Google credentials.
- Do not break the existing OAuth and calendar-read flows while adding prioritization.
- Prefer incremental additions over large refactors.
- Update tests whenever features or contracts change.
- Keep `README.md` aligned with actual implementation, not aspirational scope.

## Practical Status Summary

Right now the project is best understood as:

"Google Calendar OAuth + calendar/event read API with session persistence."

It is not yet the full "calendar priority API" promised in `OLD_README.md`.

Future work should close that gap by layering event prioritization on top of the existing authenticated calendar backend.