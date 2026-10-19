"""Unit tests for the volatile ticket repository."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from resolveia.domain.tickets import Ticket, TicketStatus
from resolveia.infrastructure.repositories import InMemoryTicketRepository


def test_stores_ticket_by_identifier() -> None:
    ticket = Ticket(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        title="Webhook not received",
        description="The payment succeeded but its webhook was not delivered.",
        product="Payments API",
        product_version=None,
        status=TicketStatus.RECEIVED,
        created_at=datetime(2026, 10, 19, 14, 30, tzinfo=UTC),
    )
    repository = InMemoryTicketRepository()

    asyncio.run(repository.add(ticket))

    assert repository.count == 1
    assert asyncio.run(repository.get(ticket.id)) == ticket


def test_returns_none_when_ticket_does_not_exist() -> None:
    repository = InMemoryTicketRepository()
    missing_id = UUID("df4771d9-33e9-4203-a267-cf3bcf0776d7")

    assert asyncio.run(repository.get(missing_id)) is None
    assert repository.count == 0
