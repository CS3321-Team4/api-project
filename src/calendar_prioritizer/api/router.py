from fastapi import APIRouter

from calendar_prioritizer.api.routes import auth, calendars

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(calendars.router)
