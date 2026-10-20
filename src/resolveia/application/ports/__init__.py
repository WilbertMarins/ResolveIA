"""Ports required by the application layer."""

from resolveia.application.ports.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)
from resolveia.application.ports.object_storage import (
    ObjectStorage,
    ObjectStorageError,
    ObjectToStore,
)
from resolveia.application.ports.readiness_check import ReadinessCheck
from resolveia.application.ports.ticket_repository import TicketRepository

__all__ = [
    "KnowledgeDocumentRepository",
    "ObjectStorage",
    "ObjectStorageError",
    "ObjectToStore",
    "ReadinessCheck",
    "TicketRepository",
]
