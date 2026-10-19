"""Persistence port for tickets."""

from typing import Protocol

from resolveia.domain.tickets import Ticket


class TicketRepository(Protocol):
    """Storage operations required by ticket use cases."""

    async def add(self, ticket: Ticket) -> None:
        """Store a new ticket."""
        ...
