"""Tests for recovery of abandoned extraction leases."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from resolveia.application.use_cases.recover_expired_extractions import (
    RecoverExpiredExtractions,
)
from resolveia.domain.knowledge import (
    DocumentStatus,
    DocumentType,
    ExtractedSegment,
    KnowledgeDocument,
    OutboxEvent,
)

DOCUMENT_ID = UUID("d39a3706-fd8e-4c93-b550-221e3b7d8a91")
EVENT_ID = UUID("ad61a936-cedf-4cf9-821c-c4e7c6044996")
NOW = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)


def expired_document(attempts: int = 1) -> KnowledgeDocument:
    pending = KnowledgeDocument(
        id=DOCUMENT_ID,
        original_filename="manual.txt",
        content_type="text/plain",
        extension=".txt",
        size_bytes=17,
        checksum_sha256="a" * 64,
        product="payments-api",
        product_version=None,
        document_version="2026.10",
        document_type=DocumentType.MANUAL,
        language="pt-BR",
        valid_until=None,
        storage_bucket="resolveia-knowledge",
        storage_key=f"documents/{DOCUMENT_ID}/original.txt",
        status=DocumentStatus.PENDING_INGESTION,
        failure_reason=None,
        created_at=NOW - timedelta(minutes=10),
        updated_at=NOW - timedelta(minutes=10),
        extraction_attempts=attempts - 1,
    )
    return pending.start_processing(
        NOW - timedelta(minutes=6),
        NOW - timedelta(minutes=1),
    )


class RecoveryRepository:
    def __init__(self, document: KnowledgeDocument) -> None:
        self.document = document
        self.event: OutboxEvent | None = None

    async def claim(
        self,
        document_id: UUID,
        started_at: datetime,
        lease_until: datetime,
    ) -> KnowledgeDocument | None:
        return None

    async def complete(
        self,
        document: KnowledgeDocument,
        segments: list[ExtractedSegment],
    ) -> bool:
        return False

    async def update_claimed(self, document: KnowledgeDocument) -> bool:
        if self.document.status is not DocumentStatus.PROCESSING:
            return False
        self.document = document
        return True

    async def list_expired(
        self,
        expired_before: datetime,
        limit: int,
    ) -> list[KnowledgeDocument]:
        lease_until = self.document.processing_lease_until
        if lease_until is not None and lease_until <= expired_before:
            return [self.document][:limit]
        return []

    async def recover_with_event(
        self,
        document: KnowledgeDocument,
        event: OutboxEvent,
    ) -> bool:
        self.document = document
        self.event = event
        return True


def test_recovers_expired_lease_and_creates_new_event() -> None:
    repository = RecoveryRepository(expired_document())

    result = asyncio.run(
        RecoverExpiredExtractions(
            repository,
            batch_size=100,
            maximum_attempts=3,
            clock=lambda: NOW,
            event_id_factory=lambda: EVENT_ID,
        ).execute()
    )

    assert result.recovered == 1
    assert repository.document.status is DocumentStatus.PENDING_INGESTION
    assert repository.event is not None
    assert repository.event.aggregate_id == DOCUMENT_ID


def test_marks_expired_document_failed_after_maximum_attempts() -> None:
    repository = RecoveryRepository(expired_document(attempts=3))

    result = asyncio.run(
        RecoverExpiredExtractions(
            repository,
            batch_size=100,
            maximum_attempts=3,
            clock=lambda: NOW,
        ).execute()
    )

    assert result.exhausted == 1
    assert repository.document.status is DocumentStatus.INGESTION_FAILED
    assert repository.document.failure_reason == "extraction_attempts_exhausted"
