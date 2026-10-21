"""Executable loop for recovery and transactional-outbox delivery."""

import asyncio
import logging
from pathlib import Path
from tempfile import gettempdir

from sqlalchemy.exc import SQLAlchemyError

from resolveia.application.use_cases.dispatch_outbox import DispatchOutbox
from resolveia.application.use_cases.recover_expired_extractions import (
    RecoverExpiredExtractions,
)
from resolveia.infrastructure.config import get_settings
from resolveia.infrastructure.database import (
    PostgresExtractionRepository,
    PostgresOutboxRepository,
    create_database,
)
from resolveia.infrastructure.messaging.celery_app import celery_app
from resolveia.infrastructure.messaging.publisher import CeleryTaskPublisher

HEARTBEAT_PATH = Path(gettempdir()) / "resolveia-dispatcher-heartbeat"
logger = logging.getLogger(__name__)


async def dispatch_once() -> None:
    """Recover abandoned work and publish one bounded outbox batch."""
    settings = get_settings()
    engine, session_factory = create_database(settings.database_url.get_secret_value())
    try:
        async with session_factory() as session:
            extraction_repository = PostgresExtractionRepository(session)
            await RecoverExpiredExtractions(
                extraction_repository,
                settings.outbox_batch_size,
                settings.extraction_maximum_attempts,
            ).execute()
            await DispatchOutbox(
                PostgresOutboxRepository(session),
                CeleryTaskPublisher(celery_app),
                settings.outbox_batch_size,
            ).execute()
    finally:
        await engine.dispose()


async def run_dispatcher() -> None:
    """Continuously dispatch events and maintain a process heartbeat."""
    settings = get_settings()
    while True:
        try:
            await dispatch_once()
        except SQLAlchemyError:
            logger.warning("outbox_dispatch_database_unavailable")
        else:
            HEARTBEAT_PATH.touch()
        await asyncio.sleep(settings.outbox_poll_interval_seconds)


def main() -> None:
    """Run the dispatcher until its process receives an interruption."""
    asyncio.run(run_dispatcher())


if __name__ == "__main__":
    main()
