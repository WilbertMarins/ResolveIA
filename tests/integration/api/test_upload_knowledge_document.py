"""HTTP contract tests for knowledge-document uploads."""

from datetime import date
from uuid import UUID

from fastapi.testclient import TestClient

from resolveia.application.ports import ObjectStorageError, ObjectToStore
from resolveia.application.use_cases import MAX_FILE_SIZE_BYTES
from resolveia.domain.knowledge import DocumentStatus, KnowledgeDocument
from resolveia.infrastructure.repositories import InMemoryTicketRepository
from resolveia.presentation.api.app import create_app


class InMemoryDocumentRepository:
    """Keep the latest document state for API assertions."""

    def __init__(self) -> None:
        self.documents: dict[UUID, KnowledgeDocument] = {}

    async def add(self, document: KnowledgeDocument) -> None:
        self.documents[document.id] = document

    async def update(self, document: KnowledgeDocument) -> None:
        self.documents[document.id] = document


class InMemoryObjectStorage:
    """Capture object uploads without network I/O."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.items: list[ObjectToStore] = []

    async def put(self, item: ObjectToStore) -> None:
        if self.fail:
            raise ObjectStorageError("secret provider detail")
        self.items.append(item)


def create_test_client(
    repository: InMemoryDocumentRepository,
    storage: InMemoryObjectStorage,
) -> TestClient:
    api = create_app(
        repository=InMemoryTicketRepository(),
        knowledge_document_repository=repository,
        object_storage=storage,
    )
    return TestClient(api)


def valid_form() -> dict[str, str]:
    return {
        "product": "payments-api",
        "product_version": "2.4",
        "document_version": "2026.10",
        "document_type": "runbook",
        "language": "pt-BR",
        "valid_until": "2027-10-31",
    }


def test_upload_returns_public_metadata_without_storage_location() -> None:
    repository = InMemoryDocumentRepository()
    storage = InMemoryObjectStorage()

    with create_test_client(repository, storage) as client:
        response = client.post(
            "/api/v1/knowledge/documents",
            data=valid_form(),
            files={"file": ("../payments-api.md", b"# Synthetic API", "text/markdown")},
        )

    body = response.json()
    assert response.status_code == 201
    assert body["original_filename"] == "payments-api.md"
    assert body["status"] == "pending_ingestion"
    assert body["size_bytes"] == 15
    assert "storage_bucket" not in body
    assert "storage_key" not in body
    assert len(storage.items) == 1


def test_rejects_invalid_pdf_before_upload() -> None:
    repository = InMemoryDocumentRepository()
    storage = InMemoryObjectStorage()

    with create_test_client(repository, storage) as client:
        response = client.post(
            "/api/v1/knowledge/documents",
            data=valid_form(),
            files={"file": ("manual.pdf", b"invalid", "application/pdf")},
        )

    assert response.status_code == 400
    assert storage.items == []
    assert repository.documents == {}


def test_rejects_file_above_limit_before_upload() -> None:
    repository = InMemoryDocumentRepository()
    storage = InMemoryObjectStorage()

    with create_test_client(repository, storage) as client:
        response = client.post(
            "/api/v1/knowledge/documents",
            data=valid_form(),
            files={
                "file": (
                    "manual.txt",
                    b"x" * (MAX_FILE_SIZE_BYTES + 1),
                    "text/plain",
                )
            },
        )

    assert response.status_code == 413
    assert storage.items == []
    assert repository.documents == {}


def test_rejects_invalid_language_as_unprocessable() -> None:
    repository = InMemoryDocumentRepository()
    storage = InMemoryObjectStorage()
    form = valid_form()
    form["language"] = "not_a_language"

    with create_test_client(repository, storage) as client:
        response = client.post(
            "/api/v1/knowledge/documents",
            data=form,
            files={"file": ("manual.txt", b"Synthetic content", "text/plain")},
        )

    assert response.status_code == 422
    assert storage.items == []


def test_rejects_past_validity_as_unprocessable() -> None:
    repository = InMemoryDocumentRepository()
    storage = InMemoryObjectStorage()
    form = valid_form()
    form["valid_until"] = date(2000, 1, 1).isoformat()

    with create_test_client(repository, storage) as client:
        response = client.post(
            "/api/v1/knowledge/documents",
            data=form,
            files={"file": ("manual.txt", b"Synthetic content", "text/plain")},
        )

    assert response.status_code == 422
    assert storage.items == []


def test_storage_failure_returns_sanitized_service_unavailable() -> None:
    repository = InMemoryDocumentRepository()
    storage = InMemoryObjectStorage(fail=True)

    with create_test_client(repository, storage) as client:
        response = client.post(
            "/api/v1/knowledge/documents",
            data=valid_form(),
            files={"file": ("manual.txt", b"Synthetic content", "text/plain")},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "Object storage is unavailable"}
    persisted = next(iter(repository.documents.values()))
    assert persisted.status is DocumentStatus.UPLOAD_FAILED
    assert "secret" not in response.text
