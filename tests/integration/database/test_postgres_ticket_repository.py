"""Integration tests for PostgreSQL ticket persistence."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete

from resolveia.domain.tickets import Ticket, TicketStatus
from resolveia.infrastructure.config import get_settings
from resolveia.infrastructure.database import (
    PostgresTicketRepository,
    SessionFactory,
    create_database,
)
from resolveia.infrastructure.database.models import TicketModel

TICKET_ID = UUID("a6cda672-d7f7-49e1-9e9a-31a9206ff723")
MISSING_TICKET_ID = UUID("0e225df8-a7a8-42a8-ad39-bdb1a6961247")


def make_ticket() -> Ticket:
    """Build a deterministic ticket for PostgreSQL tests."""
    return Ticket(
        id=TICKET_ID,
        title="Webhook not received",
        description="The payment succeeded but its webhook was not delivered.",
        product="Payments API",
        product_version=None,
        status=TicketStatus.RECEIVED,
        created_at=datetime(2026, 10, 19, 14, 30, tzinfo=UTC),
    )


async def remove_ticket(session_factory: SessionFactory, ticket_id: UUID) -> None:
    """Remove only the row owned by this integration test."""
    async with session_factory() as session:
        await session.execute(delete(TicketModel).where(TicketModel.id == ticket_id))
        await session.commit()


async def persist_and_reload_ticket() -> None:
    database_url = get_settings().database_url.get_secret_value()
    engine, session_factory = create_database(database_url)
    ticket = make_ticket()
    try:
        await remove_ticket(session_factory, ticket.id)
        async with session_factory() as session:
            await PostgresTicketRepository(session).add(ticket)

        async with session_factory() as session:
            restored_ticket = await PostgresTicketRepository(session).get(ticket.id)

        assert restored_ticket == ticket
        assert restored_ticket is not None
        assert restored_ticket.product_version is None
        assert restored_ticket.created_at.utcoffset() is not None
    finally:
        await remove_ticket(session_factory, ticket.id)
        await engine.dispose()


async def query_missing_ticket() -> None:
    database_url = get_settings().database_url.get_secret_value()
    engine, session_factory = create_database(database_url)
    try:
        await remove_ticket(session_factory, MISSING_TICKET_ID)
        async with session_factory() as session:
            ticket = await PostgresTicketRepository(session).get(MISSING_TICKET_ID)
        assert ticket is None
    finally:
        await engine.dispose()


def test_persists_and_reloads_ticket_across_sessions() -> None:
    asyncio.run(persist_and_reload_ticket())


def test_returns_none_for_missing_ticket() -> None:
    asyncio.run(query_missing_ticket())
