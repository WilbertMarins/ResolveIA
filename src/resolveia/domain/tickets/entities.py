"""Entities and invariants for technical support tickets."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from resolveia.domain.tickets.enums import TicketStatus

TITLE_MIN_LENGTH = 5
TITLE_MAX_LENGTH = 200
DESCRIPTION_MIN_LENGTH = 20
DESCRIPTION_MAX_LENGTH = 5_000
PRODUCT_MIN_LENGTH = 2
PRODUCT_MAX_LENGTH = 100
PRODUCT_VERSION_MIN_LENGTH = 1
PRODUCT_VERSION_MAX_LENGTH = 50


class TicketValidationError(ValueError):
    """Raised when a ticket violates a domain invariant."""


def _validate_text(value: str, field_name: str, minimum: int, maximum: int) -> None:
    if value != value.strip():
        raise TicketValidationError(f"{field_name} must not have surrounding whitespace")
    if not minimum <= len(value) <= maximum:
        raise TicketValidationError(
            f"{field_name} length must be between {minimum} and {maximum} characters"
        )


@dataclass(frozen=True, slots=True)
class Ticket:
    """A technical support request accepted by ResolveIA."""

    id: UUID
    title: str
    description: str
    product: str
    product_version: str | None
    status: TicketStatus
    created_at: datetime

    def __post_init__(self) -> None:
        """Protect invariants regardless of the entry point used to create a ticket."""
        _validate_text(self.title, "title", TITLE_MIN_LENGTH, TITLE_MAX_LENGTH)
        _validate_text(
            self.description,
            "description",
            DESCRIPTION_MIN_LENGTH,
            DESCRIPTION_MAX_LENGTH,
        )
        _validate_text(self.product, "product", PRODUCT_MIN_LENGTH, PRODUCT_MAX_LENGTH)
        if self.product_version is not None:
            _validate_text(
                self.product_version,
                "product_version",
                PRODUCT_VERSION_MIN_LENGTH,
                PRODUCT_VERSION_MAX_LENGTH,
            )
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise TicketValidationError("created_at must include timezone information")
        if self.created_at.utcoffset() != timedelta(0):
            raise TicketValidationError("created_at must use UTC")
