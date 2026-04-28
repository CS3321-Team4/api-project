# Calendar Priority API

A FastAPI app for Google Calendar OAuth 2.0 sign-in, calendar/event retrieval, priority updates, and a browser dashboard. This version includes a working server-side OAuth flow, session persistence, user-scoped calendar read endpoints, event color updates, priority-based event color mapping, and a frontend served by the same FastAPI process.

## Implemented Features

- Google OAuth 2.0 sign-in flow for end users
- Server-side session persistence backed by SQLite via SQLAlchemy
- List the authenticated user's calendars
- Get one calendar by ID
- List events for a specific calendar
- Get a single event from a specific calendar
- Update a specific event's Google Calendar color
- Update an event priority from 1 through 5 using mapped Google Calendar colors
- Read the current event priority from its Google Calendar color
- Browser dashboard for signing in, selecting a calendar, viewing events by priority, and changing event priority
- Session status and logout endpoints
- FastAPI test coverage for auth and calendar routes

## API Endpoints

### Frontend and app health

```http
GET /
GET /health
```

`/` serves the browser dashboard. `/health` returns a JSON health response.

### Auth

```http
GET /api/auth/google/url
GET /api/auth/google/login
GET /api/auth/google/callback
GET /api/auth/me
POST /api/auth/logout
```

`/api/auth/google/login` redirects the browser to Google.

`/api/auth/google/url` returns the Google authorization URL as JSON if you want a frontend to control navigation.

`/api/auth/google/callback` exchanges the authorization code, stores the Google tokens server-side, and creates a signed session cookie.

### Calendars

```http
GET /api/calendars
GET /api/calendars/{calendar_id}
GET /api/calendars/{calendar_id}/events
GET /api/calendars/{calendar_id}/events/{event_id}
PATCH /api/calendars/{calendar_id}/events/{event_id}
PATCH /api/calendars/{calendar_id}/events/{event_id}/priority/{priority_id}
GET /api/calendars/{calendar_id}/events/{event_id}/priority/
```

### Priority Mapping

```text
1 -> Google colorId 9  (blue)
2 -> Google colorId 10 (green)
3 -> Google colorId 5  (yellow)
4 -> Google colorId 6  (orange)
5 -> Google colorId 11 (red)
```

If an event's `color_id` is not one of those five Google colors, the priority endpoint returns `null` for `priority`.

## Required Secrets

Since you're using Doppler, these are the secrets you should add there:

```env
SESSION_SECRET=replace-with-a-long-random-string
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost/api/auth/google/callback
DATABASE_URL=sqlite:///./app.db
GOOGLE_OAUTH_SUCCESS_REDIRECT=http://localhost/
GOOGLE_SCOPES=openid,email,profile,https://www.googleapis.com/auth/calendar
```

Minimum required for the integration to run:

- `SESSION_SECRET`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`

Optional but useful:

- `DATABASE_URL`
- `GOOGLE_OAUTH_SUCCESS_REDIRECT`
- `GOOGLE_SCOPES`

## Doppler Setup

Example workflow:

```bash
doppler secrets set SESSION_SECRET="replace-with-a-long-random-string"
doppler secrets set GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
doppler secrets set GOOGLE_CLIENT_SECRET="your-google-client-secret"
doppler secrets set GOOGLE_REDIRECT_URI="http://localhost/api/auth/google/callback"
doppler secrets set DATABASE_URL="sqlite:///./app.db"
```

Then run the API through Doppler:

```bash
doppler run -- uv run uvicorn --app-dir src calendar_prioritizer.main:app --host 0.0.0.0 --port 80 --reload
```

If you use Docker locally, run Docker through Doppler as well:

```bash
doppler run -- docker compose up --build
```

The container project root is `/src/calendar-prioritizer`, and the Python package now lives at `src/calendar_prioritizer`.

## Google Cloud Configuration

In the Google Cloud Console, create a Web application OAuth client and add this redirect URI for local development:

```text
http://localhost/api/auth/google/callback
```

If you deploy this API, the deployed callback URL must also be added to the same OAuth client.

## Local Development

1. Install dependencies.

```bash
uv sync
```

2. Start the API with Doppler.

```bash
doppler run -- uv run uvicorn --app-dir src calendar_prioritizer.main:app --host 0.0.0.0 --port 80 --reload
```

3. Open the dashboard.

```text
http://localhost/
```

4. Open the docs.

```text
http://localhost/docs
```

5. Start authentication.

Use the dashboard's Google sign-in button, or open:

```text
http://localhost/api/auth/google/login
```

or call:

```http
GET /api/auth/google/url
```

## Useful Request Examples

List calendars after signing in:

```bash
curl -b cookies.txt -c cookies.txt http://localhost/api/calendars
```

List events from the primary calendar:

```bash
curl -b cookies.txt -c cookies.txt "http://localhost/api/calendars/primary/events?single_events=true&order_by=startTime"
```

Set an event to priority 5:

```bash
curl -X PATCH -b cookies.txt -c cookies.txt http://localhost/api/calendars/primary/events/event-1/priority/5
```

Read an event's priority:

```bash
curl -b cookies.txt -c cookies.txt http://localhost/api/calendars/primary/events/event-1/priority/
```

## Tests

```bash
uv run pytest
```

## GitHub Actions

The repository includes `.github/workflows/ci.yml`, which follows the professor's CI/CD shape:

- `Coverage` installs dependencies with `uv sync --frozen`, runs pytest through coverage, and requires at least 80% coverage.
- `Build & Push` runs only for `main` pushes or manual dispatches, builds the wheel, fetches Docker credentials from Doppler, tags the Docker image as `latest` and the commit SHA, and pushes both tags.
- `Deploy` runs after a successful image push, fetches deployment secrets from Doppler, SSHes into AWS, pulls the latest image, and restarts the container.

GitHub needs one repository secret:

```text
DOPPLER_GH_SERVICE_TOKEN
```

Doppler should provide these deployment secrets:

```text
DOCKER_USERNAME
DOCKER_PASSWORD
DOCKER_IMAGE
AWS_IP
AWS_EC2_USERNAME
SSH_AWS_PEM
SESSION_SECRET
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI
GOOGLE_OAUTH_SUCCESS_REDIRECT
GOOGLE_SCOPES
DATABASE_URL
SESSION_COOKIE_HTTPS_ONLY
```

`DOCKER_IMAGE` is optional. If it is not set, the workflow uses `DOCKER_USERNAME/calendar-prioritizer`.

For branch protection, require the `Coverage` status check before merging into `main`.

## UV Workflow

This project now uses `uv` for dependency and environment management.

```bash
uv sync
uv run uvicorn --app-dir src calendar_prioritizer.main:app --host 0.0.0.0 --port 80 --reload
uv run pytest
```

## Notes

- OAuth tokens are stored server-side in the configured database.
- The default scope includes writable Google Calendar access so event color and priority updates can be pushed to Google.
- The session cookie is signed, and the OAuth state parameter is validated during callback.
- For production, set `SESSION_COOKIE_HTTPS_ONLY=true` and use a strong `SESSION_SECRET`.
- Binding to port 80 can require administrator privileges on some local machines.
