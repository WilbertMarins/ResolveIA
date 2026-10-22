"""Use case for registering a source document in the knowledge base."""

import hashlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import PurePosixPath
from uuid import UUID, uuid4

from resolveia.application.exceptions import (
    InvalidKnowledgeFileError,
    KnowledgeFileTooLargeError,
    KnowledgeUploadUnavailableError,
)
from resolveia.application.messages import (
    EXTRACTION_CONTRACT_VERSION,
    EXTRACTION_EVENT_TYPE,
)
from resolveia.application.ports import (
    KnowledgeDocumentRepository,
    ObjectStorage,
    ObjectStorageError,
    ObjectToStore,
)
from resolveia.domain.knowledge import (
    DocumentStatus,
    DocumentType,
    KnowledgeDocument,
    KnowledgeDocumentValidationError,
    OutboxEvent,
)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
}
UPLOAD_FAILURE_REASON = "object_storage_upload_failed"
logger = logging.getLogger(__name__)

type DocumentIdFactory = Callable[[], UUID]
type EventIdFactory = Callable[[], UUID]
type Clock = Callable[[], datetime]


def utc_now() -> datetime:
    """Return a timezone-aware current UTC timestamp."""
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class UploadKnowledgeDocumentCommand:
    """Transport data needed to upload a source document."""

    original_filename: str
    content_type: str
    content: bytes
    product: str
    product_version: str | None
    document_version: str
    document_type: DocumentType
    language: str
    valid_until: date | None


class UploadKnowledgeDocument:
    """Persist upload state and store the original document."""

    def __init__(
        self,
        repository: KnowledgeDocumentRepository,
        object_storage: ObjectStorage,
        bucket: str,
        id_factory: DocumentIdFactory = uuid4,
        event_id_factory: EventIdFactory = uuid4,
        clock: Clock = utc_now,
    ) -> None:
        self._repository = repository
        self._object_storage = object_storage
        self._bucket = bucket
        self._id_factory = id_factory
        self._event_id_factory = event_id_factory
        self._clock = clock

    async def execute(
        self,
        command: UploadKnowledgeDocumentCommand,
    ) -> KnowledgeDocument:
        """Validate, track, and upload a source document."""
        content = command.content
        if not content:
            raise InvalidKnowledgeFileError("File must not be empty")
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise KnowledgeFileTooLargeError("File exceeds the 10 MiB limit")

        filename, extension = self._validate_file(
            command.original_filename,
            command.content_type,
            content,
        )
        created_at = self._normalized_time()
        if command.valid_until is not None and command.valid_until < created_at.date():
            raise KnowledgeDocumentValidationError("valid_until cannot be in the past")

        document_id = self._id_factory()
        checksum = hashlib.sha256(content).hexdigest()
        document = KnowledgeDocument(
            id=document_id,
            original_filename=filename,
            content_type=command.content_type,
            extension=extension,
            size_bytes=len(content),
            checksum_sha256=checksum,
            product=command.product.strip(),
            product_version=(
                command.product_version.strip() if command.product_version is not None else None
            ),
            document_version=command.document_version.strip(),
            document_type=command.document_type,
            language=command.language.strip(),
            valid_until=command.valid_until,
            storage_bucket=self._bucket,
            storage_key=f"documents/{document_id}/original{extension}",
            status=DocumentStatus.UPLOADING,
            failure_reason=None,
            created_at=created_at,
            updated_at=created_at,
        )
        await self._repository.add(document)

        upload_started_at = time.perf_counter()
        try:
            await self._object_storage.put(
                ObjectToStore(
                    bucket=document.storage_bucket,
                    key=document.storage_key,
                    content=content,
                    content_type=document.content_type,
                    metadata={
                        "document-id": str(document.id),
                        "sha256": document.checksum_sha256,
                    },
                )
            )
        except ObjectStorageError as error:
            failed_document = document.mark_upload_failed(
                self._normalized_time(),
                UPLOAD_FAILURE_REASON,
            )
            await self._repository.update(failed_document)
            logger.warning(
                "knowledge_document_upload_failed",
                extra={
                    "document_id": str(document.id),
                    "duration_seconds": time.perf_counter() - upload_started_at,
                },
            )
            raise KnowledgeUploadUnavailableError("Object storage upload failed") from error

        uploaded_document = document.mark_pending_ingestion(self._normalized_time())
        event_id = self._event_id_factory()
        event = OutboxEvent(
            id=event_id,
            event_type=EXTRACTION_EVENT_TYPE,
            aggregate_id=document.id,
            payload={
                "event_id": str(event_id),
                "document_id": str(document.id),
                "contract_version": EXTRACTION_CONTRACT_VERSION,
            },
            occurred_at=uploaded_document.updated_at,
        )
        await self._repository.complete_upload(uploaded_document, event)
        logger.info(
            "knowledge_document_upload_completed",
            extra={
                "document_id": str(document.id),
                "duration_seconds": time.perf_counter() - upload_started_at,
            },
        )
        return uploaded_document

    def _normalized_time(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise InvalidKnowledgeFileError("clock must return a timezone-aware datetime")
        return value.astimezone(UTC)

    @staticmethod
    def _validate_file(
        original_filename: str,
        content_type: str,
        content: bytes,
    ) -> tuple[str, str]:
        if any(ord(character) < 32 or ord(character) == 127 for character in original_filename):
            raise InvalidKnowledgeFileError("Filename contains control characters")

        filename = PurePosixPath(original_filename.replace("\\", "/")).name.strip()
        if not filename or len(filename) > 255:
            raise InvalidKnowledgeFileError("Filename is invalid")
        extension = PurePosixPath(filename).suffix.lower()
        expected_content_type = ALLOWED_CONTENT_TYPES.get(extension)
        if expected_content_type is None:
            raise InvalidKnowledgeFileError("File extension is not supported")
        if content_type != expected_content_type:
            raise InvalidKnowledgeFileError("Content type does not match file extension")

        if extension == ".pdf":
            if not content.startswith(b"%PDF-"):
                raise InvalidKnowledgeFileError("PDF signature is invalid")
        else:
            try:
                content.decode("utf-8")
            except UnicodeDecodeError as error:
                raise InvalidKnowledgeFileError("Text files must use UTF-8") from error

        return filename, extension
