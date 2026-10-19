"""Unit tests for the create-ticket use case."""

import asyncio
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from resolveia.application.use_cases import CreateTicket, CreateTicketCommand
from resolveia.domain.tickets import TicketStatus, TicketValidationError
from resolveia.infrastructure.repositories import InMemoryTicketRepository

TICKET_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
CREATED_AT = datetime(2026, 10, 19, 14, 30, tzinfo=UTC)


def test_creates_normalized_ticket_with_controlled_values() -> None:
    repository = InMemoryTicketRepository()
    use_case = CreateTicket(
        repository,
        id_factory=lambda: TICKET_ID,
        clock=lambda: CREATED_AT,
    )

    ticket = asyncio.run(
        use_case.execute(
            CreateTicketCommand(
                title="  Webhook not received  ",
                description="  The payment succeeded but its webhook was not delivered.  ",
                product="  Payments API  ",
                product_version="  v2  ",
            )
        )
    )

    assert ticket.id == TICKET_ID
    assert ticket.title == "Webhook not received"
    assert ticket.description == "The payment succeeded but its webhook was not delivered."
    assert ticket.product == "Payments API"
    assert ticket.product_version == "v2"
    assert ticket.status is TicketStatus.RECEIVED
    assert ticket.created_at == CREATED_AT
    assert asyncio.run(repository.get(TICKET_ID)) == ticket


def test_converts_aware_clock_value_to_utc() -> None:
    local_time = datetime(
        2026,
        10,
        19,
        10,
        30,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    use_case = CreateTicket(
        InMemoryTicketRepository(),
        id_factory=lambda: TICKET_ID,
        clock=lambda: local_time,
    )

    ticket = asyncio.run(
        use_case.execute(
            CreateTicketCommand(
                title="Webhook not received",
                description="The payment succeeded but its webhook was not delivered.",
                product="Payments API",
            )
        )
    )

    assert ticket.created_at == CREATED_AT


def test_rejects_naive_clock_value() -> None:
    use_case = CreateTicket(
        InMemoryTicketRepository(),
        id_factory=lambda: TICKET_ID,
        clock=lambda: datetime(2026, 10, 19, 14, 30),
    )

    with pytest.raises(TicketValidationError, match="timezone-aware"):
        asyncio.run(
            use_case.execute(
                CreateTicketCommand(
                    title="Webhook not received",
                    description="The payment succeeded but its webhook was not delivered.",
                    product="Payments API",
                )
            )
        )
