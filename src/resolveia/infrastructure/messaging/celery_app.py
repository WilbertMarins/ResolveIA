"""Celery application configured for the extraction worker."""

from celery import Celery

from resolveia.application.messages import EXTRACTION_TASK_NAME
from resolveia.infrastructure.config import get_settings

settings = get_settings()

celery_app = Celery(
    "resolveia",
    broker=settings.celery_broker_url.get_secret_value(),
    include=["resolveia.infrastructure.messaging.tasks"],
)
celery_app.conf.update(
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    broker_transport_options={"confirm_publish": True},
    result_backend=None,
    task_acks_late=True,
    task_default_queue="knowledge-extraction",
    task_ignore_result=True,
    task_reject_on_worker_lost=True,
    task_routes={EXTRACTION_TASK_NAME: {"queue": "knowledge-extraction"}},
    task_serializer="json",
    task_soft_time_limit=settings.extraction_soft_time_limit_seconds,
    task_time_limit=settings.extraction_hard_time_limit_seconds,
)
