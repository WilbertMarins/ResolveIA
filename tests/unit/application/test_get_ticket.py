"""Unit tests for the get-ticket use case."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

import pytest

from resolveia.application.exceptions import TicketNotFoundError
from resolveia.application.use_cases import GetTicket
from resolveia.domain.tickets import Ticket, TicketStatus
from resolveia.infrastructure.repositories import InMemoryTicketRepository

TICKET_ID = UUID("550e8400-e29b-41d4-a716-446655440000")


def make_ticket() -> Ticket:
    """Build a valid ticket for application tests."""
    return Ticket(
        id=TICKET_ID,
        title="Webhook not received",
        description="The payment succeeded but its webhook was not delivered.",
        product="Payments API",
        product_version="v2",
        status=TicketStatus.RECEIVED,
        created_at=datetime(2026, 10, 19, 14, 30, tzinfo=UTC),
    )


def test_returns_stored_ticket() -> None:
    repository = InMemoryTicketRepository()
    expected_ticket = make_ticket()
    asyncio.run(repository.add(expected_ticket))

    ticket = asyncio.run(GetTicket(repository).execute(TICKET_ID))

    assert ticket == expected_ticket
    assert repository.count == 1


def test_raises_application_error_when_ticket_does_not_exist() -> None:
    repository = InMemoryTicketRepository()

    with pytest.raises(TicketNotFoundError) as captured_error:
        asyncio.run(GetTicket(repository).execute(TICKET_ID))

    assert captured_error.value.ticket_id == TICKET_ID
    assert repository.count == 0
