"""Use case for idempotent source-document extraction."""

import hashlib
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from resolveia.application.exceptions import TransientExtractionError
from resolveia.application.messages import ExtractionRequestedMessage
from resolveia.application.ports import (
    DocumentExtractionError,
    DocumentExtractor,
    ExtractionRepository,
    ObjectStorage,
    ObjectStorageError,
    ObjectStorageNotFoundError,
)
from resolveia.application.use_cases.upload_knowledge_document import MAX_FILE_SIZE_BYTES
from resolveia.domain.knowledge import (
    ExtractedSegment,
    ExtractionFailureCode,
    KnowledgeDocument,
)

logger = logging.getLogger(__name__)

type SegmentIdFactory = Callable[[], UUID]
type Clock = Callable[[], datetime]


class ExtractionOutcome(StrEnum):
    """Observable result of handling an extraction message."""

    EXTRACTED = "extracted"
    FAILED = "failed"
    SKIPPED = "skipped"


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(UTC)


class ProcessDocumentExtraction:
    """Claim, download, extract, and atomically persist normalized segments."""

    def __init__(
        self,
        repository: ExtractionRepository,
        object_storage: ObjectStorage,
        extractor: DocumentExtractor,
        lease_seconds: int,
        segment_id_factory: SegmentIdFactory = uuid4,
        clock: Clock = utc_now,
    ) -> None:
        self._repository = repository
        self._object_storage = object_storage
        self._extractor = extractor
        self._lease_seconds = lease_seconds
        self._segment_id_factory = segment_id_factory
        self._clock = clock
        self._active_document: KnowledgeDocument | None = None

    async def execute(
        self,
        message: ExtractionRequestedMessage,
        final_attempt: bool = False,
    ) -> ExtractionOutcome:
        """Process one at-least-once message without duplicating extracted data."""
        started_at = self._now()
        document = await self._repository.claim(
            message.document_id,
            started_at,
            started_at + timedelta(seconds=self._lease_seconds),
        )
        if document is None:
            return ExtractionOutcome.SKIPPED
        self._active_document = document

        extraction_started_at = time.perf_counter()
        try:
            content = await self._object_storage.get(
                document.storage_bucket,
                document.storage_key,
                MAX_FILE_SIZE_BYTES,
            )
        except ObjectStorageNotFoundError:
            return await self._fail(
                document,
                ExtractionFailureCode.SOURCE_OBJECT_NOT_FOUND,
                extraction_started_at,
            )
        except ObjectStorageError as error:
            if final_attempt:
                return await self._fail(
                    document,
                    ExtractionFailureCode.ATTEMPTS_EXHAUSTED,
                    extraction_started_at,
                )
            updated = await self._repository.update_claimed(document.release_for_retry(self._now()))
            if not updated:
                return ExtractionOutcome.SKIPPED
            raise TransientExtractionError("source object is temporarily unavailable") from error

        try:
            extracted_texts = self._extractor.extract(content, document.extension)
        except DocumentExtractionError as error:
            return await self._fail(document, error.code, extraction_started_at)

        completed_at = self._now()
        segments = [
            self._build_segment(
                document.id,
                item.ordinal,
                item.page_number,
                item.content,
                completed_at,
            )
            for item in extracted_texts
        ]
        extracted_document = document.mark_extracted(completed_at)
        if not await self._repository.complete(extracted_document, segments):
            return ExtractionOutcome.SKIPPED
        logger.info(
            "knowledge_document_extraction_completed",
            extra={
                "event_id": str(message.event_id),
                "document_id": str(message.document_id),
                "previous_state": document.status.value,
                "new_state": extracted_document.status.value,
                "attempt": extracted_document.extraction_attempts,
                "segment_count": len(segments),
                "character_count": sum(segment.character_count for segment in segments),
                "duration_seconds": time.perf_counter() - extraction_started_at,
            },
        )
        return ExtractionOutcome.EXTRACTED

    async def fail_active_timeout(self) -> None:
        """Fail the claim owned by this use-case instance after a soft timeout."""
        if self._active_document is not None:
            await self._repository.update_claimed(
                self._active_document.mark_ingestion_failed(
                    self._now(),
                    ExtractionFailureCode.TIMEOUT.value,
                )
            )

    async def _fail(
        self,
        document: KnowledgeDocument,
        code: ExtractionFailureCode,
        started_at: float,
    ) -> ExtractionOutcome:
        failed_document = document.mark_ingestion_failed(self._now(), code.value)
        if not await self._repository.update_claimed(failed_document):
            return ExtractionOutcome.SKIPPED
        logger.warning(
            "knowledge_document_extraction_failed",
            extra={
                "document_id": str(document.id),
                "previous_state": document.status.value,
                "new_state": failed_document.status.value,
                "attempt": failed_document.extraction_attempts,
                "result": code.value,
                "duration_seconds": time.perf_counter() - started_at,
            },
        )
        return ExtractionOutcome.FAILED

    def _build_segment(
        self,
        document_id: UUID,
        ordinal: int,
        page_number: int | None,
        content: str,
        created_at: datetime,
    ) -> ExtractedSegment:
        return ExtractedSegment(
            id=self._segment_id_factory(),
            document_id=document_id,
            ordinal=ordinal,
            page_number=page_number,
            content=content,
            character_count=len(content),
            content_checksum_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            created_at=created_at,
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value.astimezone(UTC)
