"""Enumerations used by the ticket domain."""

from enum import StrEnum


class TicketStatus(StrEnum):
    """Lifecycle states supported by a ticket."""

    RECEIVED = "received"
