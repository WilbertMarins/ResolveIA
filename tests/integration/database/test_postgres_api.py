"""Integration test for API persistence across application lifecycles."""

import asyncio
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import delete

from resolveia.infrastructure.config import get_settings
from resolveia.infrastructure.database import create_database
from resolveia.infrastructure.database.models import TicketModel
from resolveia.presentation.api.app import create_app

PAYLOAD = {
    "title": "Webhook de pagamento não recebido",
    "description": "O pagamento foi confirmado, mas nosso endpoint não recebeu o webhook.",
    "product": "Payments API",
    "product_version": "v2",
}


async def remove_ticket(ticket_id: UUID) -> None:
    database_url = get_settings().database_url.get_secret_value()
    engine, session_factory = create_database(database_url)
    try:
        async with session_factory() as session:
            await session.execute(delete(TicketModel).where(TicketModel.id == ticket_id))
            await session.commit()
    finally:
        await engine.dispose()


def test_ticket_survives_api_restart() -> None:
    with TestClient(create_app()) as client:
        create_response = client.post("/api/v1/tickets", json=PAYLOAD)

    ticket_id = UUID(create_response.json()["id"])
    try:
        with TestClient(create_app()) as restarted_client:
            get_response = restarted_client.get(create_response.headers["location"])

        assert create_response.status_code == 201
        assert get_response.status_code == 200
        assert get_response.json() == create_response.json()
    finally:
        asyncio.run(remove_ticket(ticket_id))
