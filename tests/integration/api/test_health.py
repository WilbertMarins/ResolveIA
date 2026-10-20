"""HTTP tests for liveness and readiness endpoints."""

from fastapi.testclient import TestClient

from resolveia.infrastructure.repositories import InMemoryTicketRepository
from resolveia.presentation.api.app import create_app


class FakeReadinessCheck:
    """Return a deterministic readiness result and record calls."""

    def __init__(self, available: bool) -> None:
        self.available = available
        self.calls = 0

    async def check(self) -> bool:
        self.calls += 1
        return self.available


class UnexpectedReadinessCheck:
    """Fail if liveness accidentally checks external infrastructure."""

    async def check(self) -> bool:
        raise AssertionError("Liveness must not execute readiness checks")


def test_liveness_does_not_check_dependencies() -> None:
    api = create_app(
        repository=InMemoryTicketRepository(),
        readiness_check=UnexpectedReadinessCheck(),
    )

    with TestClient(api) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_reports_available_database() -> None:
    check = FakeReadinessCheck(available=True)
    api = create_app(repository=InMemoryTicketRepository(), readiness_check=check)

    with TestClient(api) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "available"},
    }
    assert check.calls == 1


def test_readiness_reports_unavailable_database_without_details() -> None:
    check = FakeReadinessCheck(available=False)
    api = create_app(repository=InMemoryTicketRepository(), readiness_check=check)

    with TestClient(api) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "unavailable"},
    }
    assert "postgresql" not in response.text
    assert "secret" not in response.text
    assert check.calls == 1
