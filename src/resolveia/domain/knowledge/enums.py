"""Enumerations used by knowledge documents."""

from enum import StrEnum


class DocumentType(StrEnum):
    """Supported categories of technical documentation."""

    MANUAL = "manual"
    RUNBOOK = "runbook"
    FAQ = "faq"
    TROUBLESHOOTING = "troubleshooting"
    RELEASE_NOTES = "release_notes"
    POLICY = "policy"


class DocumentStatus(StrEnum):
    """Initial upload and ingestion states."""

    UPLOADING = "uploading"
    PENDING_INGESTION = "pending_ingestion"
    UPLOAD_FAILED = "upload_failed"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    INGESTION_FAILED = "ingestion_failed"


class ExtractionFailureCode(StrEnum):
    """Sanitized permanent extraction failure reasons."""

    SOURCE_OBJECT_NOT_FOUND = "source_object_not_found"
    ENCRYPTED_PDF = "encrypted_pdf"
    INVALID_PDF = "invalid_pdf"
    NO_EXTRACTABLE_TEXT = "no_extractable_text"
    PAGE_LIMIT_EXCEEDED = "extraction_page_limit_exceeded"
    CHARACTER_LIMIT_EXCEEDED = "extraction_character_limit_exceeded"
    TIMEOUT = "extraction_timeout"
    ATTEMPTS_EXHAUSTED = "extraction_attempts_exhausted"
