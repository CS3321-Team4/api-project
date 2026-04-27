from __future__ import annotations

from contextlib import asynccontextmanager
<<<<<<< HEAD
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
=======

from fastapi import FastAPI
>>>>>>> dev
from starlette.middleware.sessions import SessionMiddleware

from calendar_prioritizer.api.router import api_router
from calendar_prioritizer.core.config import Settings, get_settings
from calendar_prioritizer.db.session import create_engine_from_settings, create_session_factory, init_db

<<<<<<< HEAD
STATIC_DIR = Path(__file__).parent / "static"

=======
>>>>>>> dev

def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = create_engine_from_settings(app_settings)
        session_factory = create_session_factory(engine)
        init_db(engine)

        app.state.settings = app_settings
        app.state.engine = engine
        app.state.session_factory = session_factory

        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=app_settings.session_secret,
        session_cookie=app_settings.session_cookie_name,
        max_age=app_settings.session_max_age_seconds,
        same_site=app_settings.session_cookie_same_site,
        https_only=app_settings.session_cookie_https_only,
    )
    app.include_router(api_router, prefix=app_settings.api_v1_prefix)
<<<<<<< HEAD
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def read_root() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")
=======

    @app.get("/")
    def read_root() -> dict[str, str]:
        return {
            "message": f"{app_settings.app_name} is running",
            "docs_url": "/docs",
            "api_prefix": app_settings.api_v1_prefix,
        }
>>>>>>> dev

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
