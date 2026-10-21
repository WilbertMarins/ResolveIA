"""PostgreSQL repository adapters."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from resolveia.domain.knowledge import (
    DocumentStatus,
    ExtractedSegment,
    ExtractionSummary,
    KnowledgeDocument,
    OutboxEvent,
)
from resolveia.domain.tickets import Ticket
from resolveia.infrastructure.database.models import (
    ExtractedSegmentModel,
    KnowledgeDocumentModel,
    OutboxEventModel,
    TicketModel,
)


class PostgresTicketRepository:
    """Persist tickets with a request-scoped SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, ticket: Ticket) -> None:
        """Store and commit a new ticket."""
        self._session.add(TicketModel.from_domain(ticket))
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def get(self, ticket_id: UUID) -> Ticket | None:
        """Return a domain ticket by identifier or None."""
        model = await self._session.get(TicketModel, ticket_id)
        return model.to_domain() if model is not None else None


class PostgresKnowledgeDocumentRepository:
    """Persist knowledge-document metadata with a request-scoped session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, document: KnowledgeDocument) -> None:
        """Store and commit the initial upload state."""
        self._session.add(KnowledgeDocumentModel.from_domain(document))
        await self._commit()

    async def update(self, document: KnowledgeDocument) -> None:
        """Merge and commit a document lifecycle transition."""
        await self._session.merge(KnowledgeDocumentModel.from_domain(document))
        await self._commit()

    async def complete_upload(
        self,
        document: KnowledgeDocument,
        event: OutboxEvent,
    ) -> None:
        """Commit upload completion and its extraction request together."""
        await self._session.merge(KnowledgeDocumentModel.from_domain(document))
        self._session.add(OutboxEventModel.from_domain(event))
        await self._commit()

    async def get(self, document_id: UUID) -> KnowledgeDocument | None:
        """Return knowledge-document metadata by identifier."""
        model = await self._session.get(KnowledgeDocumentModel, document_id)
        return model.to_domain() if model is not None else None

    async def get_extraction_summary(
        self,
        document_id: UUID,
    ) -> ExtractionSummary | None:
        """Aggregate extracted segments without returning their content."""
        document = await self._session.get(KnowledgeDocumentModel, document_id)
        if document is None or document.extracted_at is None:
            return None
        result = await self._session.execute(
            select(
                func.count(ExtractedSegmentModel.id),
                func.sum(ExtractedSegmentModel.character_count),
            ).where(ExtractedSegmentModel.document_id == document_id)
        )
        segment_count, character_count = result.one()
        if not segment_count or not character_count:
            return None
        return ExtractionSummary(
            segment_count=int(segment_count),
            character_count=int(character_count),
            extracted_at=document.extracted_at,
        )

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise


class PostgresExtractionRepository:
    """Coordinate extraction transitions with row-level locking."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def claim(
        self,
        document_id: UUID,
        started_at: datetime,
        lease_until: datetime,
    ) -> KnowledgeDocument | None:
        model = await self._locked_document(document_id)
        if model is None or model.status != DocumentStatus.PENDING_INGESTION.value:
            await self._session.rollback()
            return None
        document = model.to_domain().start_processing(started_at, lease_until)
        await self._session.merge(KnowledgeDocumentModel.from_domain(document))
        await self._commit()
        return document

    async def complete(
        self,
        document: KnowledgeDocument,
        segments: list[ExtractedSegment],
    ) -> bool:
        model = await self._locked_document(document.id)
        if not self._owns_claim(model, document):
            await self._session.rollback()
            return False
        await self._session.merge(KnowledgeDocumentModel.from_domain(document))
        self._session.add_all(
            [ExtractedSegmentModel.from_domain(segment) for segment in segments]
        )
        await self._commit()
        return True

    async def update_claimed(self, document: KnowledgeDocument) -> bool:
        model = await self._locked_document(document.id)
        if not self._owns_claim(model, document):
            await self._session.rollback()
            return False
        await self._session.merge(KnowledgeDocumentModel.from_domain(document))
        await self._commit()
        return True

    async def list_expired(
        self,
        expired_before: datetime,
        limit: int,
    ) -> list[KnowledgeDocument]:
        result = await self._session.scalars(
            select(KnowledgeDocumentModel)
            .where(
                KnowledgeDocumentModel.status == DocumentStatus.PROCESSING.value,
                KnowledgeDocumentModel.processing_lease_until <= expired_before,
            )
            .order_by(KnowledgeDocumentModel.processing_lease_until)
            .limit(limit)
        )
        return [model.to_domain() for model in result]

    async def recover_with_event(
        self,
        document: KnowledgeDocument,
        event: OutboxEvent,
    ) -> bool:
        model = await self._locked_document(document.id)
        if (
            model is None
            or model.status != DocumentStatus.PROCESSING.value
            or model.processing_lease_until is None
            or model.processing_lease_until > event.occurred_at
        ):
            await self._session.rollback()
            return False
        await self._session.merge(KnowledgeDocumentModel.from_domain(document))
        self._session.add(OutboxEventModel.from_domain(event))
        await self._commit()
        return True

    async def _locked_document(self, document_id: UUID) -> KnowledgeDocumentModel | None:
        return await self._session.scalar(
            select(KnowledgeDocumentModel)
            .where(KnowledgeDocumentModel.id == document_id)
            .with_for_update()
        )

    @staticmethod
    def _owns_claim(
        model: KnowledgeDocumentModel | None,
        proposed: KnowledgeDocument,
    ) -> bool:
        return (
            model is not None
            and model.status == DocumentStatus.PROCESSING.value
            and model.extraction_attempts == proposed.extraction_attempts
        )

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise


class PostgresOutboxRepository:
    """Persist and query durable task-publication events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_pending(self, limit: int) -> list[OutboxEvent]:
        result = await self._session.scalars(
            select(OutboxEventModel)
            .where(OutboxEventModel.published_at.is_(None))
            .order_by(OutboxEventModel.occurred_at)
            .limit(limit)
        )
        return [model.to_domain() for model in result]

    async def update(self, event: OutboxEvent) -> None:
        values: dict[str, object] = {
            "publish_attempts": OutboxEventModel.publish_attempts + 1,
            "last_failure_reason": event.last_failure_reason,
        }
        if event.published_at is not None:
            values["published_at"] = event.published_at
        await self._session.execute(
            update(OutboxEventModel)
            .where(
                OutboxEventModel.id == event.id,
                OutboxEventModel.published_at.is_(None),
            )
            .values(**values)
        )
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
