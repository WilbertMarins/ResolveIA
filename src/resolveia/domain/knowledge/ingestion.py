"""Domain values for durable knowledge-document ingestion."""

import hashlib
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from uuid import UUID


class IngestionValidationError(ValueError):
    """Raised when an ingestion value violates a domain invariant."""


@dataclass(frozen=True, slots=True)
class ExtractedSegment:
    """One normalized source unit before retrieval chunking."""

    id: UUID
    document_id: UUID
    ordinal: int
    page_number: int | None
    content: str
    character_count: int
    content_checksum_sha256: str
    created_at: datetime

    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise IngestionValidationError("ordinal cannot be negative")
        if self.page_number is not None and self.page_number < 1:
            raise IngestionValidationError("page_number must start at one")
        if not self.content or self.content != self.content.strip():
            raise IngestionValidationError("content must be non-empty and trimmed")
        if self.character_count != len(self.content):
            raise IngestionValidationError("character_count must match content length")
        expected_checksum = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        if self.content_checksum_sha256 != expected_checksum:
            raise IngestionValidationError("content checksum does not match content")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() != timedelta(0):
            raise IngestionValidationError("created_at must use UTC")


@dataclass(frozen=True, slots=True)
class ExtractionSummary:
    """Public-safe aggregate information about extracted content."""

    segment_count: int
    character_count: int
    extracted_at: datetime

    def __post_init__(self) -> None:
        if self.segment_count < 1 or self.character_count < 1:
            raise IngestionValidationError("extraction summary counts must be positive")
        if self.extracted_at.tzinfo is None or self.extracted_at.utcoffset() != timedelta(0):
            raise IngestionValidationError("extracted_at must use UTC")


@dataclass(frozen=True, slots=True)
class OutboxEvent:
    """Durable request to publish one versioned integration event."""

    id: UUID
    event_type: str
    aggregate_id: UUID
    payload: dict[str, str | int]
    occurred_at: datetime
    published_at: datetime | None = None
    publish_attempts: int = 0
    last_failure_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.event_type or self.event_type != self.event_type.strip():
            raise IngestionValidationError("event_type must be non-empty and trimmed")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() != timedelta(0):
            raise IngestionValidationError("occurred_at must use UTC")
        if self.published_at is not None and (
            self.published_at.tzinfo is None or self.published_at.utcoffset() != timedelta(0)
        ):
            raise IngestionValidationError("published_at must use UTC")
        if self.publish_attempts < 0:
            raise IngestionValidationError("publish_attempts cannot be negative")
        if self.published_at is not None and self.last_failure_reason is not None:
            raise IngestionValidationError("published events cannot retain a failure reason")

    def mark_published(self, published_at: datetime) -> "OutboxEvent":
        """Return an event acknowledged by the broker publisher."""
        return replace(
            self,
            published_at=published_at,
            publish_attempts=self.publish_attempts + 1,
            last_failure_reason=None,
        )

    def mark_publish_failed(self, reason: str) -> "OutboxEvent":
        """Record a sanitized failed publication attempt."""
        return replace(
            self,
            publish_attempts=self.publish_attempts + 1,
            last_failure_reason=reason,
        )
