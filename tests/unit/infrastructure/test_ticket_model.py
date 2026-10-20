"""Unit tests for mappings between ticket domain and persistence models."""

from datetime import UTC, datetime
from uuid import UUID

from resolveia.domain.tickets import Ticket, TicketStatus
from resolveia.infrastructure.database.models import TicketModel


def make_ticket(product_version: str | None = "v2") -> Ticket:
    """Build a ticket for mapping tests."""
    return Ticket(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        title="Webhook not received",
        description="The payment succeeded but its webhook was not delivered.",
        product="Payments API",
        product_version=product_version,
        status=TicketStatus.RECEIVED,
        created_at=datetime(2026, 10, 19, 14, 30, tzinfo=UTC),
    )


def test_maps_domain_ticket_to_model_and_back() -> None:
    ticket = make_ticket()

    model = TicketModel.from_domain(ticket)
    restored_ticket = model.to_domain()

    assert restored_ticket == ticket
    assert model.status == "received"


def test_preserves_missing_product_version() -> None:
    ticket = make_ticket(product_version=None)

    restored_ticket = TicketModel.from_domain(ticket).to_domain()

    assert restored_ticket.product_version is None
