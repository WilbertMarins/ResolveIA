"""FastAPI application factory and default ASGI application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from resolveia.application.ports import ReadinessCheck, TicketRepository
from resolveia.infrastructure.config import Settings, get_settings
from resolveia.infrastructure.database import create_database
from resolveia.infrastructure.health import PostgresReadinessCheck, StaticReadinessCheck
from resolveia.presentation.api.routes.health import router as health_router
from resolveia.presentation.api.routes.tickets import router as tickets_router


def create_app(
    repository: TicketRepository | None = None,
    settings: Settings | None = None,
    readiness_check: ReadinessCheck | None = None,
) -> FastAPI:
    """Create an isolated API instance with replaceable infrastructure."""

    @asynccontextmanager
    async def lifespan(api: FastAPI) -> AsyncIterator[None]:
        if repository is not None:
            api.state.readiness_check = (
                readiness_check if readiness_check is not None else StaticReadinessCheck(True)
            )
            yield
            return

        resolved_settings = settings if settings is not None else get_settings()
        engine, session_factory = create_database(
            resolved_settings.database_url.get_secret_value()
        )
        api.state.session_factory = session_factory
        api.state.readiness_check = (
            readiness_check
            if readiness_check is not None
            else PostgresReadinessCheck(
                session_factory,
                resolved_settings.database_health_timeout_seconds,
            )
        )
        try:
            yield
        finally:
            await engine.dispose()

    api = FastAPI(
        title="ResolveIA API",
        description="Multi-agent technical support for a fictional payment API.",
        version="0.1.0",
        lifespan=lifespan,
    )
    api.state.ticket_repository_override = repository
    api.include_router(health_router)
    api.include_router(tickets_router, prefix="/api/v1")
    return api


app = create_app()
