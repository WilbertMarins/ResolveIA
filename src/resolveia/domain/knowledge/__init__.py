"""Knowledge-base domain model."""

from resolveia.domain.knowledge.entities import (
    KnowledgeDocument,
    KnowledgeDocumentValidationError,
)
from resolveia.domain.knowledge.enums import (
    DocumentStatus,
    DocumentType,
    ExtractionFailureCode,
)
from resolveia.domain.knowledge.ingestion import (
    ExtractedSegment,
    ExtractionSummary,
    IngestionValidationError,
    OutboxEvent,
)

__all__ = [
    "DocumentStatus",
    "DocumentType",
    "ExtractedSegment",
    "ExtractionFailureCode",
    "ExtractionSummary",
    "IngestionValidationError",
    "KnowledgeDocument",
    "KnowledgeDocumentValidationError",
    "OutboxEvent",
]
