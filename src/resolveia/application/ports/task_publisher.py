"""Asynchronous-task publication boundary."""

from typing import Protocol

from resolveia.application.messages import ExtractionRequestedMessage


class TaskPublishError(RuntimeError):
    """Raised when a task cannot be confirmed by the broker."""


class TaskPublisher(Protocol):
    """Publish versioned extraction tasks without exposing Celery."""

    async def publish(self, message: ExtractionRequestedMessage) -> None:
        """Publish one task or raise TaskPublishError."""
        ...
