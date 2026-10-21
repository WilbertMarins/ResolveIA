"""Versioned messages crossing the ingestion boundary."""

from dataclasses import dataclass
from uuid import UUID

from resolveia.domain.knowledge import OutboxEvent

EXTRACTION_EVENT_TYPE = "knowledge.document.extraction_requested"
EXTRACTION_TASK_NAME = "knowledge.extract_document.v1"
EXTRACTION_CONTRACT_VERSION = 1


class InvalidExtractionMessageError(ValueError):
    """Raised when an extraction message has an unsupported contract."""


@dataclass(frozen=True, slots=True)
class ExtractionRequestedMessage:
    """Minimal versioned request to extract one source document."""

    event_id: UUID
    document_id: UUID
    contract_version: int = EXTRACTION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.contract_version != EXTRACTION_CONTRACT_VERSION:
            raise InvalidExtractionMessageError("unsupported extraction contract version")

    def to_payload(self) -> dict[str, str | int]:
        """Serialize the stable broker contract."""
        return {
            "event_id": str(self.event_id),
            "document_id": str(self.document_id),
            "contract_version": self.contract_version,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> "ExtractionRequestedMessage":
        """Validate untrusted broker data before starting infrastructure work."""
        try:
            event_id = UUID(str(payload["event_id"]))
            document_id = UUID(str(payload["document_id"]))
            contract_version = int(str(payload["contract_version"]))
        except (KeyError, TypeError, ValueError) as error:
            raise InvalidExtractionMessageError("invalid extraction message") from error
        return cls(
            event_id=event_id,
            document_id=document_id,
            contract_version=contract_version,
        )

    @classmethod
    def from_event(cls, event: OutboxEvent) -> "ExtractionRequestedMessage":
        """Build a broker message from a durable event."""
        if event.event_type != EXTRACTION_EVENT_TYPE:
            raise InvalidExtractionMessageError("unsupported outbox event type")
        return cls.from_payload(dict(event.payload))
