from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import get_api_router
from app.core.config import get_settings


def configure_logging() -> None:
    """Configure structlog once on startup."""

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager that configures logging."""

    configure_logging()
    yield


def create_app() -> FastAPI:
    """Instantiate the FastAPI application."""

    settings = get_settings()
    application = FastAPI(
        title=settings.project_name,
        debug=settings.debug,
        version="0.1.0",
        lifespan=lifespan,
    )

    if settings.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    application.include_router(get_api_router())
    return application


app = create_app()
