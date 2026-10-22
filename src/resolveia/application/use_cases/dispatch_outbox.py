"""Use case for publishing durable extraction requests."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from resolveia.application.messages import ExtractionRequestedMessage
from resolveia.application.ports import OutboxRepository, TaskPublisher, TaskPublishError

PUBLISH_FAILURE_REASON = "broker_publish_failed"
type Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class DispatchResult:
    """Counts from one finite outbox dispatch pass."""

    published: int
    failed: int


class DispatchOutbox:
    """Publish pending outbox events with at-least-once semantics."""

    def __init__(
        self,
        repository: OutboxRepository,
        publisher: TaskPublisher,
        batch_size: int,
        clock: Clock = utc_now,
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        self._batch_size = batch_size
        self._clock = clock

    async def execute(self) -> DispatchResult:
        """Attempt each pending event once and persist its outcome."""
        published = 0
        failed = 0
        for event in await self._repository.list_pending(self._batch_size):
            message = ExtractionRequestedMessage.from_event(event)
            try:
                await self._publisher.publish(message)
            except TaskPublishError:
                await self._repository.update(event.mark_publish_failed(PUBLISH_FAILURE_REASON))
                failed += 1
            else:
                await self._repository.update(event.mark_published(self._now()))
                published += 1
        return DispatchResult(published=published, failed=failed)

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value.astimezone(UTC)
