"""API routers."""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.routes import router as v1_router

__all__ = ["get_api_router"]


def get_api_router() -> APIRouter:
    """Return the main API router."""
    api = APIRouter()
    api.include_router(health_router)
    api.include_router(v1_router)
    return api
