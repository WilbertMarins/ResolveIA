"""Use case for retrieving a technical support ticket."""

from uuid import UUID

from resolveia.application.exceptions import TicketNotFoundError
from resolveia.application.ports import TicketRepository
from resolveia.domain.tickets import Ticket


class GetTicket:
    """Retrieve a ticket independently of delivery and persistence details."""

    def __init__(self, repository: TicketRepository) -> None:
        self._repository = repository

    async def execute(self, ticket_id: UUID) -> Ticket:
        """Return the requested ticket or signal its absence."""
        ticket = await self._repository.get(ticket_id)
        if ticket is None:
            raise TicketNotFoundError(ticket_id)
        return ticket
