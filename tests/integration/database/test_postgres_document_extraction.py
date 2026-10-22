"""PostgreSQL integration coverage for durable extraction state."""

import asyncio
import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete

from resolveia.application.messages import EXTRACTION_EVENT_TYPE
from resolveia.domain.knowledge import (
    DocumentStatus,
    DocumentType,
    ExtractedSegment,
    KnowledgeDocument,
    OutboxEvent,
)
from resolveia.infrastructure.config import get_settings
from resolveia.infrastructure.database import (
    PostgresExtractionRepository,
    PostgresKnowledgeDocumentRepository,
    SessionFactory,
    create_database,
)
from resolveia.infrastructure.database.models import (
    ExtractedSegmentModel,
    KnowledgeDocumentModel,
    OutboxEventModel,
)

DOCUMENT_ID = UUID("381162ac-c6d3-4d11-881d-94c0137eccc4")
EVENT_ID = UUID("6246ee6e-9df8-414b-8bfc-c749730df7e0")
SEGMENT_ID = UUID("ab56b64b-deaa-4128-8fe8-8f1ecbf9c7b5")
NOW = datetime(2026, 10, 21, 15, 0, tzinfo=UTC)


def uploading_document() -> KnowledgeDocument:
    return KnowledgeDocument(
        id=DOCUMENT_ID,
        original_filename="integration.md",
        content_type="text/markdown",
        extension=".md",
        size_bytes=17,
        checksum_sha256="a" * 64,
        product="payments-api",
        product_version="2.4",
        document_version="2026.10",
        document_type=DocumentType.RUNBOOK,
        language="pt-BR",
        valid_until=None,
        storage_bucket="resolveia-knowledge",
        storage_key=f"documents/{DOCUMENT_ID}/original.md",
        status=DocumentStatus.UPLOADING,
        failure_reason=None,
        created_at=NOW,
        updated_at=NOW,
    )


async def clean(session_factory: SessionFactory) -> None:
    async with session_factory() as session:
        await session.execute(
            delete(ExtractedSegmentModel).where(ExtractedSegmentModel.document_id == DOCUMENT_ID)
        )
        await session.execute(delete(OutboxEventModel).where(OutboxEventModel.id == EVENT_ID))
        await session.execute(
            delete(KnowledgeDocumentModel).where(KnowledgeDocumentModel.id == DOCUMENT_ID)
        )
        await session.commit()


async def exercise_extraction_persistence() -> None:
    settings = get_settings()
    engine, session_factory = create_database(settings.database_url.get_secret_value())
    await clean(session_factory)
    try:
        document = uploading_document()
        pending = document.mark_pending_ingestion(NOW + timedelta(seconds=1))
        event = OutboxEvent(
            id=EVENT_ID,
            event_type=EXTRACTION_EVENT_TYPE,
            aggregate_id=DOCUMENT_ID,
            payload={
                "event_id": str(EVENT_ID),
                "document_id": str(DOCUMENT_ID),
                "contract_version": 1,
            },
            occurred_at=pending.updated_at,
        )
        async with session_factory() as session:
            repository = PostgresKnowledgeDocumentRepository(session)
            await repository.add(document)
            await repository.complete_upload(pending, event)

        async with session_factory() as session:
            persisted_event = await session.get(OutboxEventModel, EVENT_ID)
            persisted_document = await session.get(KnowledgeDocumentModel, DOCUMENT_ID)
            assert persisted_event is not None
            assert persisted_document is not None
            assert persisted_document.status == DocumentStatus.PENDING_INGESTION.value

        async with session_factory() as session:
            repository = PostgresExtractionRepository(session)
            processing = await repository.claim(
                DOCUMENT_ID,
                NOW + timedelta(seconds=2),
                NOW + timedelta(minutes=5),
            )
            assert processing is not None
            content = "synthetic content"
            segment = ExtractedSegment(
                id=SEGMENT_ID,
                document_id=DOCUMENT_ID,
                ordinal=0,
                page_number=None,
                content=content,
                character_count=len(content),
                content_checksum_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                created_at=NOW + timedelta(seconds=3),
            )
            completed = processing.mark_extracted(NOW + timedelta(seconds=3))
            assert await repository.complete(completed, [segment]) is True

        async with session_factory() as session:
            extraction_repository = PostgresExtractionRepository(session)
            duplicate = await extraction_repository.claim(
                DOCUMENT_ID,
                NOW + timedelta(seconds=4),
                NOW + timedelta(minutes=5),
            )
            assert duplicate is None
            summary = await PostgresKnowledgeDocumentRepository(session).get_extraction_summary(
                DOCUMENT_ID
            )
            assert summary is not None
            assert summary.segment_count == 1
            assert summary.character_count == len("synthetic content")
    finally:
        await clean(session_factory)
        await engine.dispose()


def test_persists_outbox_and_completes_extraction_atomically() -> None:
    asyncio.run(exercise_extraction_persistence())
