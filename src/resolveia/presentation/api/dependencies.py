"""FastAPI dependency providers."""

from typing import Annotated, cast

from fastapi import Depends, Request

from resolveia.application.ports import TicketRepository
from resolveia.application.use_cases import CreateTicket


def get_ticket_repository(request: Request) -> TicketRepository:
    """Return the repository owned by the current application instance."""
    return cast(TicketRepository, request.app.state.ticket_repository)


def get_create_ticket(
    repository: Annotated[TicketRepository, Depends(get_ticket_repository)],
) -> CreateTicket:
    """Build the create-ticket use case with request-scoped dependencies."""
    return CreateTicket(repository)
