"""FastAPI application factory and default ASGI application."""

from fastapi import FastAPI

from resolveia.application.ports import TicketRepository
from resolveia.infrastructure.repositories import InMemoryTicketRepository
from resolveia.presentation.api.routes.tickets import router as tickets_router


def create_app(repository: TicketRepository | None = None) -> FastAPI:
    """Create an isolated API instance with replaceable infrastructure."""
    api = FastAPI(
        title="ResolveIA API",
        description="Multi-agent technical support for a fictional payment API.",
        version="0.1.0",
    )
    api.state.ticket_repository = (
        repository if repository is not None else InMemoryTicketRepository()
    )
    api.include_router(tickets_router, prefix="/api/v1")
    return api


app = create_app()
