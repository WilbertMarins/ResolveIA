"""RabbitMQ and Celery adapters for asynchronous ingestion."""

from resolveia.infrastructure.messaging.publisher import CeleryTaskPublisher

__all__ = ["CeleryTaskPublisher"]
