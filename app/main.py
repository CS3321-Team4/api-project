from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.db.session import create_engine_from_settings, create_session_factory, init_db


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

    @app.get("/")
    def read_root() -> dict[str, str]:
        return {
            "message": f"{app_settings.app_name} is running",
            "docs_url": "/docs",
            "api_prefix": app_settings.api_v1_prefix,
        }

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
