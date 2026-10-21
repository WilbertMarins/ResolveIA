"""Use cases exposed by the application layer."""

from resolveia.application.use_cases.create_ticket import CreateTicket, CreateTicketCommand
from resolveia.application.use_cases.dispatch_outbox import DispatchOutbox, DispatchResult
from resolveia.application.use_cases.get_knowledge_document import (
    GetKnowledgeDocument,
    KnowledgeDocumentDetails,
)
from resolveia.application.use_cases.get_ticket import GetTicket
from resolveia.application.use_cases.process_document_extraction import (
    ExtractionOutcome,
    ProcessDocumentExtraction,
)
from resolveia.application.use_cases.recover_expired_extractions import (
    RecoverExpiredExtractions,
    RecoveryResult,
)
from resolveia.application.use_cases.upload_knowledge_document import (
    MAX_FILE_SIZE_BYTES,
    UploadKnowledgeDocument,
    UploadKnowledgeDocumentCommand,
)

__all__ = [
    "CreateTicket",
    "CreateTicketCommand",
    "DispatchOutbox",
    "DispatchResult",
    "ExtractionOutcome",
    "GetKnowledgeDocument",
    "GetTicket",
    "KnowledgeDocumentDetails",
    "MAX_FILE_SIZE_BYTES",
    "ProcessDocumentExtraction",
    "RecoverExpiredExtractions",
    "RecoveryResult",
    "UploadKnowledgeDocument",
    "UploadKnowledgeDocumentCommand",
]
