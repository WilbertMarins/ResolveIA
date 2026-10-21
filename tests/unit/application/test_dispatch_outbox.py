"""Tests for finite transactional-outbox dispatch passes."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from resolveia.application.messages import EXTRACTION_EVENT_TYPE
from resolveia.application.ports import TaskPublishError
from resolveia.application.use_cases.dispatch_outbox import DispatchOutbox
from resolveia.domain.knowledge import OutboxEvent

EVENT_ID = UUID("ad61a936-cedf-4cf9-821c-c4e7c6044996")
DOCUMENT_ID = UUID("d39a3706-fd8e-4c93-b550-221e3b7d8a91")
NOW = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)


def event() -> OutboxEvent:
    return OutboxEvent(
        id=EVENT_ID,
        event_type=EXTRACTION_EVENT_TYPE,
        aggregate_id=DOCUMENT_ID,
        payload={
            "event_id": str(EVENT_ID),
            "document_id": str(DOCUMENT_ID),
            "contract_version": 1,
        },
        occurred_at=NOW,
    )


class RecordingOutboxRepository:
    def __init__(self) -> None:
        self.current = event()

    async def list_pending(self, limit: int) -> list[OutboxEvent]:
        return [self.current][:limit]

    async def update(self, current: OutboxEvent) -> None:
        self.current = current


class RecordingPublisher:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.count = 0

    async def publish(self, message: object) -> None:
        self.count += 1
        if self.fail:
            raise TaskPublishError("provider detail")


def test_marks_event_published_only_after_success() -> None:
    repository = RecordingOutboxRepository()
    publisher = RecordingPublisher()

    result = asyncio.run(
        DispatchOutbox(repository, publisher, batch_size=100, clock=lambda: NOW).execute()
    )

    assert result.published == 1
    assert repository.current.published_at == NOW
    assert repository.current.publish_attempts == 1


def test_records_sanitized_publication_failure() -> None:
    repository = RecordingOutboxRepository()
    publisher = RecordingPublisher(fail=True)

    result = asyncio.run(
        DispatchOutbox(repository, publisher, batch_size=100, clock=lambda: NOW).execute()
    )

    assert result.failed == 1
    assert repository.current.published_at is None
    assert repository.current.last_failure_reason == "broker_publish_failed"
