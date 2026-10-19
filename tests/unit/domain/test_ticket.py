"""Unit tests for ticket domain invariants."""

from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from resolveia.domain.tickets import Ticket, TicketStatus, TicketValidationError

TICKET_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
CREATED_AT = datetime(2026, 10, 19, 14, 30, tzinfo=UTC)


def make_ticket(**changes: object) -> Ticket:
    """Build a valid ticket while allowing one field to change."""
    values: dict[str, object] = {
        "id": TICKET_ID,
        "title": "Webhook not received",
        "description": "The payment succeeded but its webhook was not delivered.",
        "product": "Payments API",
        "product_version": "v2",
        "status": TicketStatus.RECEIVED,
        "created_at": CREATED_AT,
    }
    values.update(changes)
    return Ticket(**values)  # type: ignore[arg-type]


def test_accepts_valid_ticket() -> None:
    ticket = make_ticket()

    assert ticket.status is TicketStatus.RECEIVED
    assert ticket.created_at == CREATED_AT


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("title", "x" * 4),
        ("title", "x" * 201),
        ("description", "x" * 19),
        ("description", "x" * 5_001),
        ("product", "x"),
        ("product", "x" * 101),
        ("product_version", ""),
        ("product_version", "x" * 51),
    ],
)
def test_rejects_text_outside_limits(field_name: str, value: str) -> None:
    with pytest.raises(TicketValidationError):
        make_ticket(**{field_name: value})


def test_rejects_surrounding_whitespace() -> None:
    with pytest.raises(TicketValidationError, match="surrounding whitespace"):
        make_ticket(title=" Webhook not received ")


@pytest.mark.parametrize(
    "created_at",
    [
        datetime(2026, 10, 19, 14, 30),
        datetime(2026, 10, 19, 10, 30, tzinfo=timezone(timedelta(hours=-4))),
    ],
)
def test_requires_timezone_aware_utc_datetime(created_at: datetime) -> None:
    with pytest.raises(TicketValidationError):
        make_ticket(created_at=created_at)
