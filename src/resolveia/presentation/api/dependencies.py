"""FastAPI dependency providers."""

from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request

from resolveia.application.ports import ReadinessCheck, TicketRepository
from resolveia.application.use_cases import CreateTicket, GetTicket
from resolveia.infrastructure.database import PostgresTicketRepository, SessionFactory


def get_readiness_check(request: Request) -> ReadinessCheck:
    """Return the readiness check configured for this application."""
    return cast(ReadinessCheck, request.app.state.readiness_check)


async def get_ticket_repository(request: Request) -> AsyncIterator[TicketRepository]:
    """Provide an injected repository or a request-scoped PostgreSQL adapter."""
    repository = cast(
        TicketRepository | None,
        request.app.state.ticket_repository_override,
    )
    if repository is not None:
        yield repository
        return

    session_factory = cast(SessionFactory, request.app.state.session_factory)
    async with session_factory() as session:
        yield PostgresTicketRepository(session)


def get_create_ticket(
    repository: Annotated[TicketRepository, Depends(get_ticket_repository)],
) -> CreateTicket:
    """Build the create-ticket use case with request-scoped dependencies."""
    return CreateTicket(repository)


def get_get_ticket(
    repository: Annotated[TicketRepository, Depends(get_ticket_repository)],
) -> GetTicket:
    """Build the get-ticket use case with request-scoped dependencies."""
    return GetTicket(repository)
