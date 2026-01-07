"""Main FastAPI application for the A2A Self-Service platform."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from . import __version__
from .a2a import a2a_router
from .api import router
from .config import get_settings


def configure_logging() -> None:
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger = structlog.get_logger()
    logger.info("Starting A2A Self-Service platform", version=__version__)
    yield
    logger.info("Shutting down A2A Self-Service platform")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title="A2A Agent Self-Service",
        description="Self-service platform for AI agents using Google ADK with A2A protocol",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api/v1")
    app.include_router(a2a_router, prefix="/a2a", tags=["A2A Protocol"])

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/.well-known/agent.json", include_in_schema=False)
    async def well_known_agent() -> dict:
        """Well-known endpoint for platform-level agent discovery."""
        return {
            "name": "A2A Self-Service Platform",
            "description": "Platform for creating and managing AI agents",
            "url": "https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io",
            "version": __version__,
            "protocol_version": "0.1",
            "agents_endpoint": "/api/v1/agents",
            "a2a_base": "/a2a",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "a2a_selfservice.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
