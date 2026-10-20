"""PostgreSQL readiness probe."""

import asyncio

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from resolveia.infrastructure.database import SessionFactory


class PostgresReadinessCheck:
    """Check PostgreSQL availability without reading business data."""

    def __init__(self, session_factory: SessionFactory, timeout_seconds: float) -> None:
        self._session_factory = session_factory
        self._timeout_seconds = timeout_seconds

    async def check(self) -> bool:
        """Return false for expected connectivity failures and timeouts."""
        try:
            async with asyncio.timeout(self._timeout_seconds):
                await self._execute_probe()
        except (TimeoutError, OSError, SQLAlchemyError):
            return False
        return True

    async def _execute_probe(self) -> None:
        async with self._session_factory() as session:
            await session.execute(text("SELECT 1"))
