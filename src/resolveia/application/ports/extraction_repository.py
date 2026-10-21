"""Persistence boundary for document extraction workflows."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from resolveia.domain.knowledge import ExtractedSegment, KnowledgeDocument, OutboxEvent


class ExtractionRepository(Protocol):
    """Coordinate idempotent extraction state transitions."""

    async def claim(
        self,
        document_id: UUID,
        started_at: datetime,
        lease_until: datetime,
    ) -> KnowledgeDocument | None:
        """Claim a pending document or return None when no work is available."""
        ...

    async def complete(
        self,
        document: KnowledgeDocument,
        segments: list[ExtractedSegment],
    ) -> bool:
        """Complete the owned claim atomically, or reject a stale claim."""
        ...

    async def update_claimed(self, document: KnowledgeDocument) -> bool:
        """Persist a retry or failure transition only for the owned attempt."""
        ...

    async def list_expired(
        self,
        expired_before: datetime,
        limit: int,
    ) -> list[KnowledgeDocument]:
        """Return processing documents whose lease has expired."""
        ...

    async def recover_with_event(
        self,
        document: KnowledgeDocument,
        event: OutboxEvent,
    ) -> bool:
        """Recover an expired lease and enqueue it atomically when still eligible."""
        ...
