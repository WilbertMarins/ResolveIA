"""RabbitMQ integration coverage for confirmed Celery publication."""

import asyncio
from uuid import UUID

from celery import Celery

from resolveia.application.messages import (
    EXTRACTION_TASK_NAME,
    ExtractionRequestedMessage,
)
from resolveia.infrastructure.config import get_settings
from resolveia.infrastructure.messaging import CeleryTaskPublisher

EVENT_ID = UUID("f7485833-6733-40ca-bdad-caf20ec8c4e8")
DOCUMENT_ID = UUID("79dd4045-687f-4662-bb85-62300f148afa")
QUEUE_NAME = "resolveia-spec-006-integration"


async def publish(app: Celery) -> None:
    await CeleryTaskPublisher(app, queue_name=QUEUE_NAME).publish(
        ExtractionRequestedMessage(EVENT_ID, DOCUMENT_ID)
    )


def test_publishes_versioned_task_to_rabbitmq() -> None:
    settings = get_settings()
    app = Celery(
        "resolveia-integration-test",
        broker=settings.celery_broker_url.get_secret_value(),
    )
    app.conf.broker_transport_options = {"confirm_publish": True}

    asyncio.run(publish(app))

    with app.connection_for_read() as connection:
        queue = connection.SimpleQueue(QUEUE_NAME)
        try:
            broker_message = queue.get(block=True, timeout=5)
            assert broker_message.headers["task"] == EXTRACTION_TASK_NAME
            assert broker_message.headers["id"] == str(EVENT_ID)
            broker_message.ack()
        finally:
            queue.queue.delete(if_unused=False, if_empty=False)
            queue.close()
