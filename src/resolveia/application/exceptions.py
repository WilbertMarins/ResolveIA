"""Exceptions raised by application use cases."""

from uuid import UUID


class TicketNotFoundError(LookupError):
    """Raised when a ticket cannot be found by its identifier."""

    def __init__(self, ticket_id: UUID) -> None:
        self.ticket_id = ticket_id
        super().__init__(f"Ticket {ticket_id} not found")


class InvalidKnowledgeFileError(ValueError):
    """Raised when an uploaded source file does not meet its declared format."""


class KnowledgeFileTooLargeError(ValueError):
    """Raised when an uploaded source file exceeds the accepted size."""


class KnowledgeUploadUnavailableError(RuntimeError):
    """Raised when a valid upload cannot be stored in object storage."""


class KnowledgeDocumentNotFoundError(LookupError):
    """Raised when knowledge-document metadata cannot be found."""

    def __init__(self, document_id: UUID) -> None:
        self.document_id = document_id
        super().__init__(f"Knowledge document {document_id} not found")


class TransientExtractionError(RuntimeError):
    """Requests a bounded broker-managed retry for extraction."""
