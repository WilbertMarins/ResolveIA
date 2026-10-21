"""Persistence boundary for knowledge documents."""

from typing import Protocol
from uuid import UUID

from resolveia.domain.knowledge import (
    ExtractionSummary,
    KnowledgeDocument,
    OutboxEvent,
)


class KnowledgeDocumentRepository(Protocol):
    """Persist knowledge-document metadata without exposing a database API."""

    async def add(self, document: KnowledgeDocument) -> None:
        """Store a new knowledge document."""
        ...

    async def update(self, document: KnowledgeDocument) -> None:
        """Persist a lifecycle transition for an existing document."""
        ...

    async def complete_upload(
        self,
        document: KnowledgeDocument,
        event: OutboxEvent,
    ) -> None:
        """Persist upload completion and its ingestion event atomically."""
        ...

    async def get(self, document_id: UUID) -> KnowledgeDocument | None:
        """Return a document by identifier or None."""
        ...

    async def get_extraction_summary(
        self,
        document_id: UUID,
    ) -> ExtractionSummary | None:
        """Return aggregate extraction metadata when extraction completed."""
        ...
