"""Integration tests for the create-ticket HTTP endpoint."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from resolveia.infrastructure.repositories import InMemoryTicketRepository
from resolveia.presentation.api.app import create_app

VALID_PAYLOAD: dict[str, object] = {
    "title": "Webhook de pagamento não recebido",
    "description": "O pagamento foi confirmado, mas nosso endpoint não recebeu o webhook.",
    "product": "Payments API",
    "product_version": "v2",
}


@contextmanager
def api_client() -> Iterator[tuple[TestClient, InMemoryTicketRepository]]:
    """Create an isolated API and expose its repository for assertions."""
    repository = InMemoryTicketRepository()
    with TestClient(create_app(repository)) as client:
        yield client, repository


def test_creates_ticket() -> None:
    with api_client() as (client, repository):
        response = client.post("/api/v1/tickets", json=VALID_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    ticket_id = UUID(body["id"])
    assert response.headers["location"] == f"/api/v1/tickets/{ticket_id}"
    assert body["title"] == VALID_PAYLOAD["title"]
    assert body["description"] == VALID_PAYLOAD["description"]
    assert body["product"] == VALID_PAYLOAD["product"]
    assert body["product_version"] == VALID_PAYLOAD["product_version"]
    assert body["status"] == "received"
    assert datetime.fromisoformat(body["created_at"]).utcoffset() is not None
    assert repository.count == 1


def test_accepts_unknown_product_version() -> None:
    payload = {key: value for key, value in VALID_PAYLOAD.items() if key != "product_version"}

    with api_client() as (client, repository):
        response = client.post("/api/v1/tickets", json=payload)

    assert response.status_code == 201
    assert response.json()["product_version"] is None
    assert repository.count == 1


def test_normalizes_surrounding_whitespace() -> None:
    payload = {
        key: f"  {value}  " if isinstance(value, str) else value
        for key, value in VALID_PAYLOAD.items()
    }

    with api_client() as (client, _repository):
        response = client.post("/api/v1/tickets", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == VALID_PAYLOAD["title"]
    assert body["description"] == VALID_PAYLOAD["description"]
    assert body["product"] == VALID_PAYLOAD["product"]
    assert body["product_version"] == VALID_PAYLOAD["product_version"]


@pytest.mark.parametrize("missing_field", ["title", "description", "product"])
def test_rejects_missing_required_field(missing_field: str) -> None:
    payload = {key: value for key, value in VALID_PAYLOAD.items() if key != missing_field}

    with api_client() as (client, repository):
        response = client.post("/api/v1/tickets", json=payload)

    assert response.status_code == 422
    assert repository.count == 0


@pytest.mark.parametrize("empty_field", ["title", "description", "product"])
def test_rejects_whitespace_only_required_field(empty_field: str) -> None:
    payload = {**VALID_PAYLOAD, empty_field: "   "}

    with api_client() as (client, repository):
        response = client.post("/api/v1/tickets", json=payload)

    assert response.status_code == 422
    assert repository.count == 0


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("title", "x" * 4),
        ("title", "x" * 201),
        ("description", "x" * 19),
        ("description", "x" * 5_001),
        ("product", "x"),
        ("product", "x" * 101),
        ("product_version", "x" * 51),
    ],
)
def test_rejects_text_outside_limits(field_name: str, invalid_value: str) -> None:
    payload = {**VALID_PAYLOAD, field_name: invalid_value}

    with api_client() as (client, repository):
        response = client.post("/api/v1/tickets", json=payload)

    assert response.status_code == 422
    assert repository.count == 0


def test_rejects_unknown_field() -> None:
    payload = {**VALID_PAYLOAD, "priority": "high"}

    with api_client() as (client, repository):
        response = client.post("/api/v1/tickets", json=payload)

    assert response.status_code == 422
    assert repository.count == 0
