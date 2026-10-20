"""Schemas for knowledge-document HTTP operations."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from resolveia.domain.knowledge import DocumentStatus, DocumentType


class KnowledgeDocumentResponse(BaseModel):
    """Public metadata returned after a source document upload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    product: str
    product_version: str | None
    document_version: str
    document_type: DocumentType
    language: str
    valid_until: date | None
    status: DocumentStatus
    created_at: datetime
