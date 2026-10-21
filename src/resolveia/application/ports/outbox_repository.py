"""Persistence boundary for durable integration events."""

from typing import Protocol

from resolveia.domain.knowledge import OutboxEvent


class OutboxRepository(Protocol):
    """Read and record publication attempts for pending outbox events."""

    async def list_pending(self, limit: int) -> list[OutboxEvent]:
        """Return the oldest unpublished events up to the requested limit."""
        ...

    async def update(self, event: OutboxEvent) -> None:
        """Persist the latest publication outcome."""
        ...
