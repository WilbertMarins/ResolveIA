"""Exceptions raised by application use cases."""

from uuid import UUID


class TicketNotFoundError(LookupError):
    """Raised when a ticket cannot be found by its identifier."""

    def __init__(self, ticket_id: UUID) -> None:
        self.ticket_id = ticket_id
        super().__init__(f"Ticket {ticket_id} not found")
