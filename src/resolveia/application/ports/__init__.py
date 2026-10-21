"""Ports required by the application layer."""

from resolveia.application.ports.document_extractor import (
    DocumentExtractionError,
    DocumentExtractor,
    ExtractedText,
)
from resolveia.application.ports.extraction_repository import ExtractionRepository
from resolveia.application.ports.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)
from resolveia.application.ports.object_storage import (
    ObjectStorage,
    ObjectStorageError,
    ObjectStorageNotFoundError,
    ObjectToStore,
)
from resolveia.application.ports.outbox_repository import OutboxRepository
from resolveia.application.ports.readiness_check import ReadinessCheck
from resolveia.application.ports.task_publisher import TaskPublishError, TaskPublisher
from resolveia.application.ports.ticket_repository import TicketRepository

__all__ = [
    "DocumentExtractionError",
    "DocumentExtractor",
    "ExtractedText",
    "ExtractionRepository",
    "KnowledgeDocumentRepository",
    "ObjectStorage",
    "ObjectStorageError",
    "ObjectStorageNotFoundError",
    "ObjectToStore",
    "OutboxRepository",
    "ReadinessCheck",
    "TaskPublishError",
    "TaskPublisher",
    "TicketRepository",
]
