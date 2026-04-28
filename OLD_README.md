# Calendar Priority API

A FastAPI-based backend service that integrates with Google Calendar, retrieves calendar events, allows users to assign each event a priority on a configurable scale, and maps those priorities to color-coded output for easier scheduling and visualization.

## Overview

This project was built for a software engineering course focused on practical API development, testing, refactoring, secrets management, containerization, and deployment.

The main goal of the project is to enhance calendar usability by allowing users to rank events by importance. The system pulls events from Google Calendar, stores user-defined priorities, and returns event data enriched with priority and color metadata.

## Features

- Retrieve events from Google Calendar
- Assign a priority value to an event on a 1-X scale
- Map priority values to colors
- Persist priority assignments in the backend
- Expose REST API endpoints through FastAPI
- Validate requests and responses with Pydantic
- Support secure configuration using environment variables and secret management tools
- Run tests with pytest
- Containerize the service with Docker
- Prepare the application for cloud deployment

## Tech Stack

- **Language:** Python
- **Framework:** FastAPI
- **API Style:** REST
- **Validation:** Pydantic
- **Database:** SQLite or PostgreSQL
- **Testing:** pytest
- **Secrets Management:** Doppler, GitHub Secrets
- **Containerization:** Docker
- **CI/CD:** GitHub Actions
- **External Integration:** Google Calendar API

## Project Goals

This project is intended to demonstrate:

- API design and implementation using FastAPI
- clean software architecture and refactoring practices
- integration with a third-party API
- secure handling of credentials and configuration
- automated testing and code quality practices
- containerization and deployment workflows

## How It Works

1. The application authenticates with the Google Calendar API.
2. It retrieves event data from a configured Google Calendar.
3. A user assigns a priority value to an event.
4. The backend maps that priority to a color.
5. The API returns the event with added priority and color metadata.
6. Priority assignments are stored separately so they persist across requests.

## Example Use Case

A user has several events scheduled for the week:
- team meeting
- exam review session
- project deadline
- office hours

The user can assign a priority to each event, such as:
- 1 = low
- 3 = medium
- 5 = critical

The system then maps those priorities to colors, helping the user quickly identify which events matter most.

## Priority-to-Color Mapping

Example mapping for a 1-5 scale:

- 1 → Green
- 2 → Blue
- 3 → Yellow
- 4 → Orange
- 5 → Red

This mapping can be adjusted depending on project requirements.

## API Endpoints

### Health Check
```http
GET /health
````

Returns application status.

### Get Events

```http
GET /events
```

Fetches calendar events and returns them with any stored priority/color metadata.

### Get Single Event

```http
GET /events/{event_id}
```

Returns one event by its Google Calendar event ID.

### Update Event Priority

```http
PATCH /events/{event_id}/priority
```

Updates the priority of a specific event.

Example request body:

```json
{
  "priority": 4
}
```

Example response:

```json
{
  "event_id": "abc123",
  "title": "Project Demo",
  "priority": 4,
  "color": "orange"
}
```

## Suggested Project Structure

```text
.
├── app/
│   ├── main.py
│   ├── api/routes/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <your-project-folder>
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Use Doppler to inject secrets.

Example environment variables:

```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_CALENDAR_ID=your-calendar-id
DATABASE_URL=sqlite:///./app.db
PRIORITY_MIN=1
PRIORITY_MAX=5
```

### 5. Run the application

```bash
uvicorn app.main:app --reload
```

### 6. Open the API docs

FastAPI automatically provides interactive documentation:

* `/docs`
* `/redoc`

## Google Calendar Integration

This project uses the Google Calendar API to read calendar event data.

Typical setup steps:

1. Create a Google Cloud project
2. Enable the Google Calendar API
3. Create OAuth credentials or another appropriate credential type
4. Store credentials securely using Doppler and/or environment variables
5. Configure the application to access the target calendar

## Secrets Management

To meet course requirements and follow secure development practices:

* secrets should never be hard-coded
* credentials should be managed with Doppler
* CI/CD secrets should be stored in GitHub Secrets

## Testing

Run tests with:

```bash
pytest
```

Recommended test coverage areas:

* priority validation
* color mapping
* Google Calendar service behavior
* API endpoint responses
* database persistence logic

## Code Quality

Recommended tooling:

* `black` for formatting
* `ruff` or `flake8` for linting
* `pytest-cov` for test coverage

Example commands:

```bash
black .
ruff check .
pytest --cov=app
```

## Docker

Build the container:

```bash
docker build -t calendar-priority-api .
```

Run the container:

```bash
docker run -p 8000:8000 --env-file .env calendar-priority-api
```

## Deployment

This project is designed to be deployed after testing and containerization. A typical deployment workflow includes:

* running automated tests in CI
* building a Docker image
* pushing the image or source to a hosting platform
* configuring production environment variables
* verifying the deployed health endpoint

Possible deployment targets:

* Render
* Railway
* Fly.io
* Google Cloud Run

## Future Improvements

* frontend dashboard for viewing color-coded events
* authentication for multiple users
* configurable custom color palettes
* support for writing color metadata back to Google Calendar
* analytics on event importance over time
* recurring-event-specific priority handling

## Team Workflow

Recommended workflow:

* use feature branches
* create pull requests for all changes
* require code review before merge
* keep `main` stable
* write tests for new features
* refactor regularly as the project evolves

## Course Alignment

This project supports the major goals of the course by requiring students to practice:

* Git and GitHub workflows
* Python API development
* FastAPI architecture
* secrets management
* test-driven and quality-focused development
* Docker and deployment
* collaborative software engineering

## License

This project is for educational use as part of the CS3321 - Intro to Software Engineering course.