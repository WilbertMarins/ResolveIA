"""Knowledge-base domain model."""

from resolveia.domain.knowledge.entities import (
    KnowledgeDocument,
    KnowledgeDocumentValidationError,
)
from resolveia.domain.knowledge.enums import DocumentStatus, DocumentType

__all__ = [
    "DocumentStatus",
    "DocumentType",
    "KnowledgeDocument",
    "KnowledgeDocumentValidationError",
]
