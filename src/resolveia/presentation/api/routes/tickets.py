"""Ticket HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from resolveia.application.exceptions import TicketNotFoundError
from resolveia.application.use_cases import CreateTicket, CreateTicketCommand, GetTicket
from resolveia.presentation.api.dependencies import get_create_ticket, get_get_ticket
from resolveia.presentation.api.schemas import CreateTicketRequest, TicketResponse

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: CreateTicketRequest,
    response: Response,
    use_case: Annotated[CreateTicket, Depends(get_create_ticket)],
) -> TicketResponse:
    """Register a technical support ticket."""
    ticket = await use_case.execute(
        CreateTicketCommand(
            title=payload.title,
            description=payload.description,
            product=payload.product,
            product_version=payload.product_version,
        )
    )
    response.headers["Location"] = f"/api/v1/tickets/{ticket.id}"
    return TicketResponse.model_validate(ticket)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: UUID,
    use_case: Annotated[GetTicket, Depends(get_get_ticket)],
) -> TicketResponse:
    """Return a ticket by identifier."""
    try:
        ticket = await use_case.execute(ticket_id)
    except TicketNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        ) from error
    return TicketResponse.model_validate(ticket)
