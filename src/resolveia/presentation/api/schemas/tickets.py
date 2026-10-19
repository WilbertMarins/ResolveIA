"""Schemas for ticket HTTP operations."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from resolveia.domain.tickets import TicketStatus

Title = Annotated[str, Field(min_length=5, max_length=200)]
Description = Annotated[str, Field(min_length=20, max_length=5_000)]
Product = Annotated[str, Field(min_length=2, max_length=100)]
ProductVersion = Annotated[str, Field(min_length=1, max_length=50)]


class CreateTicketRequest(BaseModel):
    """Public contract for registering a ticket."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: Title
    description: Description
    product: Product
    product_version: ProductVersion | None = None


class TicketResponse(BaseModel):
    """Public representation of a newly registered ticket."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    product: str
    product_version: str | None
    status: TicketStatus
    created_at: datetime
