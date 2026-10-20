"""FastAPI application factory and default ASGI application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from resolveia.application.ports import TicketRepository
from resolveia.infrastructure.config import Settings, get_settings
from resolveia.infrastructure.database import create_database
from resolveia.presentation.api.routes.tickets import router as tickets_router


def create_app(
    repository: TicketRepository | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    """Create an isolated API instance with replaceable infrastructure."""

    @asynccontextmanager
    async def lifespan(api: FastAPI) -> AsyncIterator[None]:
        if repository is not None:
            yield
            return

        resolved_settings = settings if settings is not None else get_settings()
        engine, session_factory = create_database(
            resolved_settings.database_url.get_secret_value()
        )
        api.state.session_factory = session_factory
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
    api.include_router(tickets_router, prefix="/api/v1")
    return api


app = create_app()
