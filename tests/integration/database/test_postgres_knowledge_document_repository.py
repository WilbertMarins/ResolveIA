"""Integration test for PostgreSQL knowledge-document persistence."""

import asyncio
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import delete

from resolveia.domain.knowledge import DocumentStatus, DocumentType, KnowledgeDocument
from resolveia.infrastructure.config import get_settings
from resolveia.infrastructure.database import (
    PostgresKnowledgeDocumentRepository,
    create_database,
)
from resolveia.infrastructure.database.models import KnowledgeDocumentModel

DOCUMENT_ID = UUID("5f080f40-1574-46a8-a81b-a2237f5c5645")
NOW = datetime(2026, 10, 19, 14, 30, tzinfo=UTC)


def build_document(status: DocumentStatus = DocumentStatus.UPLOADING) -> KnowledgeDocument:
    return KnowledgeDocument(
        id=DOCUMENT_ID,
        original_filename="payments-api.md",
        content_type="text/markdown",
        extension=".md",
        size_bytes=25,
        checksum_sha256="a" * 64,
        product="payments-api",
        product_version="2.4",
        document_version="2026.10",
        document_type=DocumentType.RUNBOOK,
        language="pt-BR",
        valid_until=date(2027, 10, 31),
        storage_bucket="resolveia-knowledge",
        storage_key=f"documents/{DOCUMENT_ID}/original.md",
        status=status,
        failure_reason=None,
        created_at=NOW,
        updated_at=NOW,
    )


async def exercise_repository() -> None:
    settings = get_settings()
    engine, session_factory = create_database(settings.database_url.get_secret_value())
    try:
        async with session_factory() as session:
            repository = PostgresKnowledgeDocumentRepository(session)
            document = build_document()
            await repository.add(document)
            pending = document.mark_pending_ingestion(NOW)
            await repository.update(pending)

        async with session_factory() as session:
            stored = await session.get(KnowledgeDocumentModel, DOCUMENT_ID)
            assert stored is not None
            assert stored.to_domain() == pending
            await session.execute(
                delete(KnowledgeDocumentModel).where(
                    KnowledgeDocumentModel.id == DOCUMENT_ID
                )
            )
            await session.commit()
    finally:
        await engine.dispose()


def test_adds_and_updates_knowledge_document() -> None:
    asyncio.run(exercise_repository())
