"""Relational models and explicit domain mappings."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from resolveia.domain.tickets import Ticket, TicketStatus
from resolveia.infrastructure.database.base import Base


class TicketModel(Base):
    """Relational representation of a support ticket."""

    __tablename__ = "tickets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(5_000), nullable=False)
    product: Mapped[str] = mapped_column(String(100), nullable=False)
    product_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @classmethod
    def from_domain(cls, ticket: Ticket) -> "TicketModel":
        """Create a persistence model from a domain entity."""
        return cls(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            product=ticket.product,
            product_version=ticket.product_version,
            status=ticket.status.value,
            created_at=ticket.created_at,
        )

    def to_domain(self) -> Ticket:
        """Reconstruct a domain entity from persisted values."""
        return Ticket(
            id=self.id,
            title=self.title,
            description=self.description,
            product=self.product,
            product_version=self.product_version,
            status=TicketStatus(self.status),
            created_at=self.created_at,
        )
