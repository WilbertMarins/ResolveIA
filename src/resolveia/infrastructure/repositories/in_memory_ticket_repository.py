"""Volatile ticket repository used before relational persistence is introduced."""

from uuid import UUID

from resolveia.domain.tickets import Ticket


class InMemoryTicketRepository:
    """Store tickets in the current process memory."""

    def __init__(self) -> None:
        self._tickets: dict[UUID, Ticket] = {}

    async def add(self, ticket: Ticket) -> None:
        """Store a ticket by its identifier."""
        self._tickets[ticket.id] = ticket

    async def get(self, ticket_id: UUID) -> Ticket | None:
        """Return a stored ticket for tests and future query use cases."""
        return self._tickets.get(ticket_id)

    @property
    def count(self) -> int:
        """Return the number of stored tickets."""
        return len(self._tickets)
