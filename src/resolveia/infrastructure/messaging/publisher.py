"""Celery-backed implementation of task publication."""

import asyncio

from celery import Celery
from kombu.exceptions import OperationalError

from resolveia.application.messages import (
    EXTRACTION_TASK_NAME,
    ExtractionRequestedMessage,
)
from resolveia.application.ports import TaskPublishError


class CeleryTaskPublisher:
    """Publish extraction requests with broker confirmation enabled."""

    def __init__(self, app: Celery, queue_name: str = "knowledge-extraction") -> None:
        self._app = app
        self._queue_name = queue_name

    async def publish(self, message: ExtractionRequestedMessage) -> None:
        """Send a versioned JSON task without blocking the async dispatcher."""
        try:
            await asyncio.to_thread(
                self._app.send_task,
                EXTRACTION_TASK_NAME,
                kwargs={"payload": message.to_payload()},
                task_id=str(message.event_id),
                queue=self._queue_name,
                retry=False,
            )
        except (OperationalError, OSError) as error:
            raise TaskPublishError("broker publication failed") from error
