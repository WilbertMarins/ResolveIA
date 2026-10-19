"""Use case for registering a technical support ticket."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from resolveia.application.ports import TicketRepository
from resolveia.domain.tickets import Ticket, TicketStatus, TicketValidationError

type TicketIdFactory = Callable[[], UUID]
type Clock = Callable[[], datetime]


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC value."""
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class CreateTicketCommand:
    """Input data required to register a ticket."""

    title: str
    description: str
    product: str
    product_version: str | None = None


class CreateTicket:
    """Create and store a ticket independently of delivery and persistence details."""

    def __init__(
        self,
        repository: TicketRepository,
        id_factory: TicketIdFactory = uuid4,
        clock: Clock = utc_now,
    ) -> None:
        self._repository = repository
        self._id_factory = id_factory
        self._clock = clock

    async def execute(self, command: CreateTicketCommand) -> Ticket:
        """Create a normalized ticket and persist it through the repository port."""
        created_at = self._clock()
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise TicketValidationError("clock must return a timezone-aware datetime")

        ticket = Ticket(
            id=self._id_factory(),
            title=command.title.strip(),
            description=command.description.strip(),
            product=command.product.strip(),
            product_version=(
                command.product_version.strip() if command.product_version is not None else None
            ),
            status=TicketStatus.RECEIVED,
            created_at=created_at.astimezone(UTC),
        )
        await self._repository.add(ticket)
        return ticket
