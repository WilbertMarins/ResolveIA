"""Ticket HTTP routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from resolveia.application.use_cases import CreateTicket, CreateTicketCommand
from resolveia.presentation.api.dependencies import get_create_ticket
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
