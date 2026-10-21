"""Use case for querying knowledge-document ingestion state."""

from dataclasses import dataclass
from uuid import UUID

from resolveia.application.exceptions import KnowledgeDocumentNotFoundError
from resolveia.application.ports import KnowledgeDocumentRepository
from resolveia.domain.knowledge import ExtractionSummary, KnowledgeDocument


@dataclass(frozen=True, slots=True)
class KnowledgeDocumentDetails:
    """Document metadata combined with a public-safe extraction summary."""

    document: KnowledgeDocument
    extraction: ExtractionSummary | None


class GetKnowledgeDocument:
    """Load document state without exposing internal storage coordinates."""

    def __init__(self, repository: KnowledgeDocumentRepository) -> None:
        self._repository = repository

    async def execute(self, document_id: UUID) -> KnowledgeDocumentDetails:
        """Return document details or raise when the identifier is unknown."""
        document = await self._repository.get(document_id)
        if document is None:
            raise KnowledgeDocumentNotFoundError(document_id)
        extraction = await self._repository.get_extraction_summary(document_id)
        return KnowledgeDocumentDetails(document=document, extraction=extraction)
