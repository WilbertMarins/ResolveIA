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
