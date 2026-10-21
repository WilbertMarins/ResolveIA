"""Use case for recovering extraction work abandoned after worker loss."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from resolveia.application.messages import (
    EXTRACTION_CONTRACT_VERSION,
    EXTRACTION_EVENT_TYPE,
)
from resolveia.application.ports import ExtractionRepository
from resolveia.domain.knowledge import ExtractionFailureCode, OutboxEvent

type Clock = Callable[[], datetime]
type EventIdFactory = Callable[[], UUID]


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    recovered: int
    exhausted: int


class RecoverExpiredExtractions:
    """Return expired leases to pending or finish exhausted documents."""

    def __init__(
        self,
        repository: ExtractionRepository,
        batch_size: int,
        maximum_attempts: int,
        clock: Clock = utc_now,
        event_id_factory: EventIdFactory = uuid4,
    ) -> None:
        self._repository = repository
        self._batch_size = batch_size
        self._maximum_attempts = maximum_attempts
        self._clock = clock
        self._event_id_factory = event_id_factory

    async def execute(self) -> RecoveryResult:
        """Recover one bounded batch of expired processing leases."""
        now = self._now()
        recovered = 0
        exhausted = 0
        for document in await self._repository.list_expired(now, self._batch_size):
            if document.extraction_attempts >= self._maximum_attempts:
                updated = await self._repository.update_claimed(
                    document.mark_ingestion_failed(
                        now,
                        ExtractionFailureCode.ATTEMPTS_EXHAUSTED.value,
                    )
                )
                exhausted += int(updated)
                continue

            pending_document = document.recover_expired_lease(now)
            event_id = self._event_id_factory()
            event = OutboxEvent(
                id=event_id,
                event_type=EXTRACTION_EVENT_TYPE,
                aggregate_id=document.id,
                payload={
                    "event_id": str(event_id),
                    "document_id": str(document.id),
                    "contract_version": EXTRACTION_CONTRACT_VERSION,
                },
                occurred_at=now,
            )
            if await self._repository.recover_with_event(pending_document, event):
                recovered += 1
        return RecoveryResult(recovered=recovered, exhausted=exhausted)

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value.astimezone(UTC)
