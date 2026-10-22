"""Thin Celery task adapters for document extraction."""

import asyncio

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.time import get_exponential_backoff_interval
from sqlalchemy.exc import SQLAlchemyError

from resolveia.application.exceptions import TransientExtractionError
from resolveia.application.messages import (
    EXTRACTION_TASK_NAME,
    ExtractionRequestedMessage,
)
from resolveia.infrastructure.config import get_settings
from resolveia.infrastructure.messaging.celery_app import celery_app
from resolveia.infrastructure.messaging.runtime import extraction_use_case


async def _process(message: ExtractionRequestedMessage, final_attempt: bool) -> None:
    settings = get_settings()
    async with extraction_use_case(settings) as use_case:
        try:
            await use_case.execute(message, final_attempt=final_attempt)
        except SoftTimeLimitExceeded:
            await use_case.fail_active_timeout()
            raise


@celery_app.task(bind=True, name=EXTRACTION_TASK_NAME)
def extract_document(task: Task, payload: dict[str, object]) -> None:
    """Validate a broker message and delegate all workflow rules to the use case."""
    message = ExtractionRequestedMessage.from_payload(payload)
    settings = get_settings()
    final_attempt = task.request.retries >= settings.extraction_maximum_attempts - 1
    try:
        asyncio.run(_process(message, final_attempt))
    except TransientExtractionError as error:
        if final_attempt:
            raise
        countdown = get_exponential_backoff_interval(
            factor=2,
            retries=task.request.retries,
            maximum=60,
            full_jitter=True,
        )
        raise task.retry(
            exc=error,
            countdown=countdown,
            max_retries=settings.extraction_maximum_attempts - 1,
        ) from error
    except SQLAlchemyError:
        sanitized_error = TransientExtractionError("database operation is temporarily unavailable")
        if final_attempt:
            raise sanitized_error from None
        countdown = get_exponential_backoff_interval(
            factor=2,
            retries=task.request.retries,
            maximum=60,
            full_jitter=True,
        )
        raise task.retry(
            exc=sanitized_error,
            countdown=countdown,
            max_retries=settings.extraction_maximum_attempts - 1,
        ) from None
