"""Integration test for the real PostgreSQL readiness probe."""

import asyncio

from resolveia.infrastructure.config import get_settings
from resolveia.infrastructure.database import create_database
from resolveia.infrastructure.health import PostgresReadinessCheck


async def check_database_readiness() -> None:
    settings = get_settings()
    engine, session_factory = create_database(settings.database_url.get_secret_value())
    try:
        check = PostgresReadinessCheck(
            session_factory,
            timeout_seconds=settings.database_health_timeout_seconds,
        )
        assert await check.check() is True
    finally:
        await engine.dispose()


def test_reports_real_postgres_as_available() -> None:
    asyncio.run(check_database_readiness())
