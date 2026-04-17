# Calendar Priority API

A FastAPI backend for Google Calendar OAuth 2.0 sign-in and calendar/event retrieval. This version now includes a working server-side OAuth flow, session persistence, and user-scoped calendar read endpoints.

## Implemented Features

- Google OAuth 2.0 sign-in flow for end users
- Server-side session persistence backed by SQLite via SQLAlchemy
- List the authenticated user's calendars
- Get one calendar by ID
- List events for a specific calendar
- Get a single event from a specific calendar
- Session status and logout endpoints
- FastAPI test coverage for auth and calendar routes

## API Endpoints

### App health

```http
GET /
GET /health
```

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
```

## Required Secrets

Since you're using Doppler, these are the secrets you should add there:

```env
SESSION_SECRET=replace-with-a-long-random-string
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
DATABASE_URL=sqlite:///./app.db
GOOGLE_OAUTH_SUCCESS_REDIRECT=http://localhost:3000
GOOGLE_SCOPES=openid,email,profile,https://www.googleapis.com/auth/calendar.readonly
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
doppler secrets set GOOGLE_REDIRECT_URI="http://localhost:8000/api/auth/google/callback"
doppler secrets set DATABASE_URL="sqlite:///./app.db"
```

Then run the API through Doppler:

```bash
doppler run -- uvicorn --app-dir src calendar_prioritizer.main:app --reload
```

If you use Docker locally, run Docker through Doppler as well:

```bash
doppler run -- docker compose up --build
```


The container project root is `/src/calendar-prioritizer`, and the Python package now lives at `src/calendar_prioritizer`.
## Google Cloud Configuration

In the Google Cloud Console, create a Web application OAuth client and add this redirect URI for local development:

```text
http://localhost:8000/api/auth/google/callback
```

If you deploy this API, the deployed callback URL must also be added to the same OAuth client.

## Local Development

1. Install dependencies.

```bash
pip install -r requirements.txt
```

2. Start the API with Doppler.

```bash
doppler run -- uvicorn --app-dir src calendar_prioritizer.main:app --reload
```

3. Open the docs.

```text
http://localhost:8000/docs
```

4. Start authentication.

Open either:

```text
http://localhost:8000/api/auth/google/login
```

or call:

```http
GET /api/auth/google/url
```

## Useful Request Examples

List calendars after signing in:

```bash
curl -b cookies.txt -c cookies.txt http://localhost:8000/api/calendars
```

List events from the primary calendar:

```bash
curl -b cookies.txt -c cookies.txt "http://localhost:8000/api/calendars/primary/events?single_events=true&order_by=startTime"
```

## Tests

```bash
pytest
```

## Notes

- OAuth tokens are stored server-side in the configured database.
- The default scope is read-only Google Calendar access.
- The session cookie is signed, and the OAuth state parameter is validated during callback.
- For production, set `SESSION_COOKIE_HTTPS_ONLY=true` and use a strong `SESSION_SECRET`.
