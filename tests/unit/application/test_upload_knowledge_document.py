"""Unit tests for the knowledge-document upload use case."""

import asyncio
import hashlib
from datetime import UTC, date, datetime
from uuid import UUID

import pytest

from resolveia.application.exceptions import (
    InvalidKnowledgeFileError,
    KnowledgeFileTooLargeError,
    KnowledgeUploadUnavailableError,
)
from resolveia.application.ports import ObjectStorageError, ObjectToStore
from resolveia.application.use_cases import (
    MAX_FILE_SIZE_BYTES,
    UploadKnowledgeDocument,
    UploadKnowledgeDocumentCommand,
)
from resolveia.domain.knowledge import DocumentStatus, DocumentType, KnowledgeDocument

DOCUMENT_ID = UUID("d39a3706-fd8e-4c93-b550-221e3b7d8a91")
NOW = datetime(2026, 10, 19, 14, 30, tzinfo=UTC)
CONTENT = b"# Payment API\n\nSynthetic runbook."


class RecordingDocumentRepository:
    """Record metadata writes in memory."""

    def __init__(self) -> None:
        self.added: list[KnowledgeDocument] = []
        self.updated: list[KnowledgeDocument] = []

    async def add(self, document: KnowledgeDocument) -> None:
        self.added.append(document)

    async def update(self, document: KnowledgeDocument) -> None:
        self.updated.append(document)


class RecordingObjectStorage:
    """Record uploads and optionally simulate a provider failure."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.items: list[ObjectToStore] = []

    async def put(self, item: ObjectToStore) -> None:
        self.items.append(item)
        if self.fail:
            raise ObjectStorageError("endpoint=http://internal secret=hidden")


def command(**changes: object) -> UploadKnowledgeDocumentCommand:
    """Build a valid command with focused overrides."""
    values: dict[str, object] = {
        "original_filename": "payments-api.md",
        "content_type": "text/markdown",
        "content": CONTENT,
        "product": " payments-api ",
        "product_version": " 2.4 ",
        "document_version": " 2026.10 ",
        "document_type": DocumentType.RUNBOOK,
        "language": "pt-BR",
        "valid_until": date(2027, 10, 31),
    }
    values.update(changes)
    return UploadKnowledgeDocumentCommand(**values)  # type: ignore[arg-type]


def build_use_case(
    repository: RecordingDocumentRepository,
    storage: RecordingObjectStorage,
) -> UploadKnowledgeDocument:
    return UploadKnowledgeDocument(
        repository,
        storage,
        "resolveia-knowledge",
        id_factory=lambda: DOCUMENT_ID,
        clock=lambda: NOW,
    )


def test_uploads_valid_document_and_marks_it_pending() -> None:
    repository = RecordingDocumentRepository()
    storage = RecordingObjectStorage()

    document = asyncio.run(build_use_case(repository, storage).execute(command()))

    assert repository.added[0].status is DocumentStatus.UPLOADING
    assert repository.updated == [document]
    assert document.status is DocumentStatus.PENDING_INGESTION
    assert document.original_filename == "payments-api.md"
    assert document.product == "payments-api"
    assert document.checksum_sha256 == hashlib.sha256(CONTENT).hexdigest()
    assert document.storage_key == f"documents/{DOCUMENT_ID}/original.md"
    assert storage.items[0].metadata == {
        "document-id": str(DOCUMENT_ID),
        "sha256": document.checksum_sha256,
    }


def test_sanitizes_client_path_without_using_it_as_storage_key() -> None:
    repository = RecordingDocumentRepository()
    storage = RecordingObjectStorage()

    document = asyncio.run(
        build_use_case(repository, storage).execute(
            command(original_filename=r"..\private\manual.md")
        )
    )

    assert document.original_filename == "manual.md"
    assert "private" not in document.storage_key


@pytest.mark.parametrize(
    ("filename", "content_type", "content"),
    [
        ("empty.md", "text/markdown", b""),
        ("manual.exe", "application/octet-stream", b"binary"),
        ("manual.pdf", "application/pdf", b"not-a-pdf"),
        ("manual.txt", "text/plain", b"\xff"),
        ("manual.md", "text/plain", CONTENT),
    ],
)
def test_rejects_invalid_files(filename: str, content_type: str, content: bytes) -> None:
    repository = RecordingDocumentRepository()
    storage = RecordingObjectStorage()

    with pytest.raises(InvalidKnowledgeFileError):
        asyncio.run(
            build_use_case(repository, storage).execute(
                command(
                    original_filename=filename,
                    content_type=content_type,
                    content=content,
                )
            )
        )

    assert repository.added == []
    assert storage.items == []


def test_rejects_file_above_limit_before_storage() -> None:
    repository = RecordingDocumentRepository()
    storage = RecordingObjectStorage()

    with pytest.raises(KnowledgeFileTooLargeError):
        asyncio.run(
            build_use_case(repository, storage).execute(
                command(content=b"x" * (MAX_FILE_SIZE_BYTES + 1))
            )
        )

    assert repository.added == []
    assert storage.items == []


def test_marks_document_failed_and_hides_provider_details() -> None:
    repository = RecordingDocumentRepository()
    storage = RecordingObjectStorage(fail=True)

    with pytest.raises(KnowledgeUploadUnavailableError) as raised:
        asyncio.run(build_use_case(repository, storage).execute(command()))

    failed = repository.updated[0]
    assert failed.status is DocumentStatus.UPLOAD_FAILED
    assert failed.failure_reason == "object_storage_upload_failed"
    assert "internal" not in str(raised.value)
    assert "secret" not in str(raised.value)
