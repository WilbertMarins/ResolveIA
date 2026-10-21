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


class ExtractionSummaryResponse(BaseModel):
    """Public counts produced by a successful extraction."""

    model_config = ConfigDict(from_attributes=True)

    segment_count: int
    character_count: int
    extracted_at: datetime


class KnowledgeDocumentDetailsResponse(KnowledgeDocumentResponse):
    """Current ingestion state without internal storage or lease details."""

    failure_reason: str | None
    extraction: ExtractionSummaryResponse | None
    updated_at: datetime
