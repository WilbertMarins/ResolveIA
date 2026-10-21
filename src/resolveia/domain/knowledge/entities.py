"""Entities and invariants for source knowledge documents."""

import re
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from uuid import UUID

from resolveia.domain.knowledge.enums import DocumentStatus, DocumentType

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
LANGUAGE_PATTERN = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")


class KnowledgeDocumentValidationError(ValueError):
    """Raised when knowledge-document metadata violates an invariant."""


def _validate_text(value: str, field_name: str, maximum: int) -> None:
    if not value or value != value.strip():
        raise KnowledgeDocumentValidationError(f"{field_name} must be non-empty and trimmed")
    if len(value) > maximum:
        raise KnowledgeDocumentValidationError(
            f"{field_name} must not exceed {maximum} characters"
        )


@dataclass(frozen=True, slots=True)
class KnowledgeDocument:
    """Metadata and lifecycle state of an uploaded source document."""

    id: UUID
    original_filename: str
    content_type: str
    extension: str
    size_bytes: int
    checksum_sha256: str
    product: str
    product_version: str | None
    document_version: str
    document_type: DocumentType
    language: str
    valid_until: date | None
    storage_bucket: str
    storage_key: str
    status: DocumentStatus
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime
    processing_started_at: datetime | None = None
    processing_lease_until: datetime | None = None
    extracted_at: datetime | None = None
    extraction_attempts: int = 0

    def __post_init__(self) -> None:
        """Protect metadata invariants independently of entry point."""
        _validate_text(self.original_filename, "original_filename", 255)
        _validate_text(self.content_type, "content_type", 100)
        _validate_text(self.extension, "extension", 10)
        _validate_text(self.product, "product", 100)
        _validate_text(self.document_version, "document_version", 50)
        _validate_text(self.language, "language", 35)
        _validate_text(self.storage_bucket, "storage_bucket", 255)
        _validate_text(self.storage_key, "storage_key", 512)
        if self.product_version is not None:
            _validate_text(self.product_version, "product_version", 50)
        if self.failure_reason is not None:
            _validate_text(self.failure_reason, "failure_reason", 100)
        if self.size_bytes <= 0:
            raise KnowledgeDocumentValidationError("size_bytes must be greater than zero")
        if SHA256_PATTERN.fullmatch(self.checksum_sha256) is None:
            raise KnowledgeDocumentValidationError("checksum_sha256 must be lowercase SHA-256")
        if LANGUAGE_PATTERN.fullmatch(self.language) is None:
            raise KnowledgeDocumentValidationError("language must be a simple BCP 47 tag")
        for field_name, value in (
            ("created_at", self.created_at),
            ("updated_at", self.updated_at),
        ):
            if value.tzinfo is None or value.utcoffset() is None:
                raise KnowledgeDocumentValidationError(f"{field_name} must include timezone")
            if value.utcoffset() != timedelta(0):
                raise KnowledgeDocumentValidationError(f"{field_name} must use UTC")
        if self.updated_at < self.created_at:
            raise KnowledgeDocumentValidationError("updated_at cannot precede created_at")
        for field_name, value in (
            ("processing_started_at", self.processing_started_at),
            ("processing_lease_until", self.processing_lease_until),
            ("extracted_at", self.extracted_at),
        ):
            if value is not None and (
                value.tzinfo is None
                or value.utcoffset() is None
                or value.utcoffset() != timedelta(0)
            ):
                raise KnowledgeDocumentValidationError(f"{field_name} must use UTC")
        if self.extraction_attempts < 0:
            raise KnowledgeDocumentValidationError("extraction_attempts cannot be negative")
        failed_statuses = {
            DocumentStatus.UPLOAD_FAILED,
            DocumentStatus.INGESTION_FAILED,
        }
        if self.status in failed_statuses and not self.failure_reason:
            raise KnowledgeDocumentValidationError("failed documents require a failure reason")
        if self.status not in failed_statuses and self.failure_reason is not None:
            raise KnowledgeDocumentValidationError(
                "failure_reason is only allowed for failed documents"
            )
        if self.status is DocumentStatus.PROCESSING:
            if self.processing_started_at is None or self.processing_lease_until is None:
                raise KnowledgeDocumentValidationError(
                    "processing documents require timestamps and a lease"
                )
            if self.processing_lease_until <= self.processing_started_at:
                raise KnowledgeDocumentValidationError(
                    "processing lease must end after processing starts"
                )
        elif self.processing_lease_until is not None:
            raise KnowledgeDocumentValidationError(
                "only processing documents can hold a processing lease"
            )
        if self.status is DocumentStatus.EXTRACTED and self.extracted_at is None:
            raise KnowledgeDocumentValidationError(
                "extracted documents require extracted_at"
            )
        if self.status is not DocumentStatus.EXTRACTED and self.extracted_at is not None:
            raise KnowledgeDocumentValidationError(
                "extracted_at is only allowed for extracted documents"
            )

    def mark_pending_ingestion(self, updated_at: datetime) -> "KnowledgeDocument":
        """Return the state reached after object storage confirms the upload."""
        if self.status is not DocumentStatus.UPLOADING:
            raise KnowledgeDocumentValidationError(
                "only uploading documents can become pending ingestion"
            )
        return replace(self, status=DocumentStatus.PENDING_INGESTION, updated_at=updated_at)

    def mark_upload_failed(
        self,
        updated_at: datetime,
        reason: str,
    ) -> "KnowledgeDocument":
        """Return a recoverable failed-upload state with a sanitized reason."""
        if self.status is not DocumentStatus.UPLOADING:
            raise KnowledgeDocumentValidationError(
                "only uploading documents can become upload failed"
            )
        return replace(
            self,
            status=DocumentStatus.UPLOAD_FAILED,
            failure_reason=reason,
            updated_at=updated_at,
        )

    def start_processing(
        self,
        started_at: datetime,
        lease_until: datetime,
    ) -> "KnowledgeDocument":
        """Claim a pending document for one extraction attempt."""
        if self.status is not DocumentStatus.PENDING_INGESTION:
            raise KnowledgeDocumentValidationError(
                "only pending documents can start processing"
            )
        return replace(
            self,
            status=DocumentStatus.PROCESSING,
            processing_started_at=started_at,
            processing_lease_until=lease_until,
            extraction_attempts=self.extraction_attempts + 1,
            updated_at=started_at,
        )

    def release_for_retry(self, updated_at: datetime) -> "KnowledgeDocument":
        """Release a processing claim before a broker-managed retry."""
        if self.status is not DocumentStatus.PROCESSING:
            raise KnowledgeDocumentValidationError(
                "only processing documents can be released for retry"
            )
        return replace(
            self,
            status=DocumentStatus.PENDING_INGESTION,
            processing_started_at=None,
            processing_lease_until=None,
            updated_at=updated_at,
        )

    def mark_extracted(self, extracted_at: datetime) -> "KnowledgeDocument":
        """Complete extraction after all normalized segments are ready."""
        if self.status is not DocumentStatus.PROCESSING:
            raise KnowledgeDocumentValidationError(
                "only processing documents can become extracted"
            )
        return replace(
            self,
            status=DocumentStatus.EXTRACTED,
            processing_lease_until=None,
            extracted_at=extracted_at,
            updated_at=extracted_at,
        )

    def mark_ingestion_failed(
        self,
        failed_at: datetime,
        reason: str,
    ) -> "KnowledgeDocument":
        """Finish a pending or processing document with a sanitized failure."""
        if self.status not in {
            DocumentStatus.PENDING_INGESTION,
            DocumentStatus.PROCESSING,
        }:
            raise KnowledgeDocumentValidationError(
                "only pending or processing documents can fail ingestion"
            )
        return replace(
            self,
            status=DocumentStatus.INGESTION_FAILED,
            failure_reason=reason,
            processing_lease_until=None,
            updated_at=failed_at,
        )

    def recover_expired_lease(self, recovered_at: datetime) -> "KnowledgeDocument":
        """Return an abandoned processing document to the pending state."""
        if self.status is not DocumentStatus.PROCESSING:
            raise KnowledgeDocumentValidationError(
                "only processing documents can recover an expired lease"
            )
        if self.processing_lease_until is None or self.processing_lease_until > recovered_at:
            raise KnowledgeDocumentValidationError("processing lease has not expired")
        return replace(
            self,
            status=DocumentStatus.PENDING_INGESTION,
            processing_started_at=None,
            processing_lease_until=None,
            updated_at=recovered_at,
        )
