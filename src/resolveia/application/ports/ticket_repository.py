"""Persistence port for tickets."""

from typing import Protocol
from uuid import UUID

from resolveia.domain.tickets import Ticket


class TicketRepository(Protocol):
    """Storage operations required by ticket use cases."""

    async def add(self, ticket: Ticket) -> None:
        """Store a new ticket."""
        ...

    async def get(self, ticket_id: UUID) -> Ticket | None:
        """Return a ticket by identifier or None when it does not exist."""
        ...
