"""API routers."""

from fastapi import APIRouter

from app.api.routes import router as api_router

__all__ = ["get_api_router"]


def get_api_router() -> APIRouter:
    """Return the main API router."""

    return api_router
