"""Document text-extraction boundary."""

from dataclasses import dataclass
from typing import Protocol

from resolveia.domain.knowledge import ExtractionFailureCode


class DocumentExtractionError(ValueError):
    """Raised for a permanent and publicly classifiable extraction failure."""

    def __init__(self, code: ExtractionFailureCode) -> None:
        self.code = code
        super().__init__(code.value)


@dataclass(frozen=True, slots=True)
class ExtractedText:
    """Provider-independent normalized text unit."""

    ordinal: int
    page_number: int | None
    content: str


class DocumentExtractor(Protocol):
    """Extract normalized text without exposing a parser implementation."""

    def extract(self, content: bytes, extension: str) -> list[ExtractedText]:
        """Return ordered text units or raise DocumentExtractionError."""
        ...
