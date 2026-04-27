FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.2 /uv /uvx /bin/

WORKDIR /src/calendar-prioritizer
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 80

CMD ["uv", "run", "uvicorn", "--app-dir", "src", "calendar_prioritizer.main:app", "--host", "0.0.0.0", "--port", "80"]
