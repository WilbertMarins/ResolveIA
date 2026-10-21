"""Tests for idempotent asynchronous document extraction."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from resolveia.application.exceptions import TransientExtractionError
from resolveia.application.messages import ExtractionRequestedMessage
from resolveia.application.ports import (
    ExtractedText,
    ObjectStorageError,
    ObjectToStore,
)
from resolveia.application.use_cases.process_document_extraction import (
    ExtractionOutcome,
    ProcessDocumentExtraction,
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
SEGMENT_ID = UUID("5e48149d-d369-4ab9-a279-b2bea98154eb")
NOW = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)


def pending_document() -> KnowledgeDocument:
    return KnowledgeDocument(
        id=DOCUMENT_ID,
        original_filename="manual.txt",
        content_type="text/plain",
        extension=".txt",
        size_bytes=17,
        checksum_sha256="a" * 64,
        product="payments-api",
        product_version="2.4",
        document_version="2026.10",
        document_type=DocumentType.MANUAL,
        language="pt-BR",
        valid_until=None,
        storage_bucket="resolveia-knowledge",
        storage_key=f"documents/{DOCUMENT_ID}/original.txt",
        status=DocumentStatus.PENDING_INGESTION,
        failure_reason=None,
        created_at=NOW,
        updated_at=NOW,
    )


class InMemoryExtractionRepository:
    def __init__(self, document: KnowledgeDocument) -> None:
        self.document = document
        self.segments: list[ExtractedSegment] = []

    async def claim(
        self,
        document_id: UUID,
        started_at: datetime,
        lease_until: datetime,
    ) -> KnowledgeDocument | None:
        if (
            document_id != self.document.id
            or self.document.status is not DocumentStatus.PENDING_INGESTION
        ):
            return None
        self.document = self.document.start_processing(started_at, lease_until)
        return self.document

    async def complete(
        self,
        document: KnowledgeDocument,
        segments: list[ExtractedSegment],
    ) -> bool:
        if self.document.status is not DocumentStatus.PROCESSING:
            return False
        self.document = document
        self.segments = segments
        return True

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
        return []

    async def recover_with_event(
        self,
        document: KnowledgeDocument,
        event: OutboxEvent,
    ) -> bool:
        return False


class StubStorage:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.reads = 0

    async def put(self, item: ObjectToStore) -> None:
        raise NotImplementedError

    async def get(self, bucket: str, key: str, maximum_bytes: int) -> bytes:
        self.reads += 1
        if self.fail:
            raise ObjectStorageError("secret endpoint detail")
        return b"synthetic content"


class StubExtractor:
    def extract(self, content: bytes, extension: str) -> list[ExtractedText]:
        return [ExtractedText(ordinal=0, page_number=None, content="synthetic content")]


def build_use_case(
    repository: InMemoryExtractionRepository,
    storage: StubStorage,
) -> ProcessDocumentExtraction:
    return ProcessDocumentExtraction(
        repository,
        storage,
        StubExtractor(),
        lease_seconds=300,
        segment_id_factory=lambda: SEGMENT_ID,
        clock=lambda: NOW + timedelta(seconds=1),
    )


def message() -> ExtractionRequestedMessage:
    return ExtractionRequestedMessage(EVENT_ID, DOCUMENT_ID)


def test_extracts_and_persists_segments_atomically() -> None:
    repository = InMemoryExtractionRepository(pending_document())
    storage = StubStorage()

    outcome = asyncio.run(build_use_case(repository, storage).execute(message()))

    assert outcome is ExtractionOutcome.EXTRACTED
    assert repository.document.status is DocumentStatus.EXTRACTED
    assert repository.document.extraction_attempts == 1
    assert repository.segments[0].id == SEGMENT_ID
    assert repository.segments[0].content == "synthetic content"


def test_skips_duplicate_message_without_reading_storage() -> None:
    document = pending_document().start_processing(
        NOW,
        NOW + timedelta(minutes=5),
    ).mark_extracted(NOW + timedelta(seconds=1))
    repository = InMemoryExtractionRepository(document)
    storage = StubStorage()

    outcome = asyncio.run(build_use_case(repository, storage).execute(message()))

    assert outcome is ExtractionOutcome.SKIPPED
    assert storage.reads == 0


def test_releases_claim_before_requesting_transient_retry() -> None:
    repository = InMemoryExtractionRepository(pending_document())
    storage = StubStorage(fail=True)

    with pytest.raises(TransientExtractionError):
        asyncio.run(build_use_case(repository, storage).execute(message()))

    assert repository.document.status is DocumentStatus.PENDING_INGESTION
    assert repository.document.failure_reason is None


def test_marks_final_transient_failure_with_sanitized_code() -> None:
    repository = InMemoryExtractionRepository(pending_document())
    storage = StubStorage(fail=True)

    outcome = asyncio.run(
        build_use_case(repository, storage).execute(message(), final_attempt=True)
    )

    assert outcome is ExtractionOutcome.FAILED
    assert repository.document.status is DocumentStatus.INGESTION_FAILED
    assert repository.document.failure_reason == "extraction_attempts_exhausted"
