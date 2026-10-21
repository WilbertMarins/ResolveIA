"""Bounded text extraction and deterministic normalization."""

import re
import unicodedata
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from resolveia.application.ports import DocumentExtractionError, ExtractedText
from resolveia.domain.knowledge import ExtractionFailureCode

MULTIPLE_BLANK_LINES = re.compile(r"\n{3,}")


def normalize_text(value: str) -> str:
    """Normalize untrusted extracted text without interpreting its meaning."""
    normalized = unicodedata.normalize("NFC", value)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "".join(
        character
        for character in normalized
        if character in {"\n", "\t"} or unicodedata.category(character) != "Cc"
    )
    normalized = "\n".join(line.rstrip(" \t") for line in normalized.split("\n"))
    normalized = MULTIPLE_BLANK_LINES.sub("\n\n", normalized)
    return normalized.strip()


class SafeDocumentExtractor:
    """Extract supported source formats under explicit resource limits."""

    def __init__(self, maximum_pages: int, maximum_characters: int) -> None:
        self._maximum_pages = maximum_pages
        self._maximum_characters = maximum_characters

    def extract(self, content: bytes, extension: str) -> list[ExtractedText]:
        """Extract normalized units or raise a sanitized permanent error."""
        if extension in {".md", ".txt"}:
            return self._extract_text(content)
        if extension == ".pdf":
            return self._extract_pdf(content)
        raise DocumentExtractionError(ExtractionFailureCode.INVALID_PDF)

    def _extract_text(self, content: bytes) -> list[ExtractedText]:
        try:
            decoded = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise DocumentExtractionError(ExtractionFailureCode.NO_EXTRACTABLE_TEXT) from error
        normalized = normalize_text(decoded)
        if not normalized:
            raise DocumentExtractionError(ExtractionFailureCode.NO_EXTRACTABLE_TEXT)
        self._enforce_character_limit(len(normalized))
        return [ExtractedText(ordinal=0, page_number=None, content=normalized)]

    def _extract_pdf(self, content: bytes) -> list[ExtractedText]:
        try:
            reader = PdfReader(BytesIO(content), strict=True)
            if reader.is_encrypted:
                raise DocumentExtractionError(ExtractionFailureCode.ENCRYPTED_PDF)
            if len(reader.pages) > self._maximum_pages:
                raise DocumentExtractionError(ExtractionFailureCode.PAGE_LIMIT_EXCEEDED)

            segments: list[ExtractedText] = []
            character_count = 0
            for page_number, page in enumerate(reader.pages, start=1):
                normalized = normalize_text(page.extract_text() or "")
                if not normalized:
                    continue
                character_count += len(normalized)
                self._enforce_character_limit(character_count)
                segments.append(
                    ExtractedText(
                        ordinal=len(segments),
                        page_number=page_number,
                        content=normalized,
                    )
                )
        except DocumentExtractionError:
            raise
        except (PdfReadError, KeyError, TypeError, ValueError) as error:
            raise DocumentExtractionError(ExtractionFailureCode.INVALID_PDF) from error

        if not segments:
            raise DocumentExtractionError(ExtractionFailureCode.NO_EXTRACTABLE_TEXT)
        return segments

    def _enforce_character_limit(self, character_count: int) -> None:
        if character_count > self._maximum_characters:
            raise DocumentExtractionError(ExtractionFailureCode.CHARACTER_LIMIT_EXCEEDED)
