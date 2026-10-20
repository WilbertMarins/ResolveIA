"""Unit tests for the PostgreSQL readiness adapter."""

import asyncio
from typing import cast

from resolveia.infrastructure.database import SessionFactory
from resolveia.infrastructure.health import PostgresReadinessCheck


class SlowReadinessCheck(PostgresReadinessCheck):
    """Probe that takes longer than its configured timeout."""

    async def _execute_probe(self) -> None:
        await asyncio.sleep(0.05)


class FailingReadinessCheck(PostgresReadinessCheck):
    """Probe that simulates an operating-system connection failure."""

    async def _execute_probe(self) -> None:
        raise OSError("postgresql://user:secret@internal-host/database")


def unused_session_factory() -> SessionFactory:
    """Provide a placeholder that overridden probes never access."""
    return cast(SessionFactory, object())


def test_returns_false_when_probe_times_out() -> None:
    check = SlowReadinessCheck(unused_session_factory(), timeout_seconds=0.001)

    assert asyncio.run(check.check()) is False


def test_returns_false_without_exposing_operational_error() -> None:
    check = FailingReadinessCheck(unused_session_factory(), timeout_seconds=1.0)

    assert asyncio.run(check.check()) is False
