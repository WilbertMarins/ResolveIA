"""Tests for bounded and deterministic source extraction."""

from io import BytesIO

import pytest
from pypdf import PdfWriter

from resolveia.application.ports import DocumentExtractionError
from resolveia.domain.knowledge import ExtractionFailureCode
from resolveia.infrastructure.extraction import SafeDocumentExtractor, normalize_text


def textual_pdf() -> bytes:
    """Build a minimal deterministic PDF with one synthetic text operation."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 100] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (b"<< /Length 39 >>\nstream\nBT /F1 12 Tf 10 50 Td (Synthetic) Tj ET\nendstream"),
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode())
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode()
    )
    return bytes(output)


def test_normalizes_text_in_the_specified_order() -> None:
    value = " Cafe\u0301  \r\nline\x00\t \r\n\r\n\r\nlast "

    assert normalize_text(value) == "Café\nline\n\nlast"


def test_extracts_one_normalized_utf8_segment() -> None:
    extractor = SafeDocumentExtractor(maximum_pages=500, maximum_characters=100)

    segments = extractor.extract(b"first  \r\n\r\n\r\nsecond", ".md")

    assert len(segments) == 1
    assert segments[0].ordinal == 0
    assert segments[0].page_number is None
    assert segments[0].content == "first\n\nsecond"


def test_rejects_text_above_the_character_limit() -> None:
    extractor = SafeDocumentExtractor(maximum_pages=500, maximum_characters=3)

    with pytest.raises(DocumentExtractionError) as raised:
        extractor.extract(b"four", ".txt")

    assert raised.value.code is ExtractionFailureCode.CHARACTER_LIMIT_EXCEEDED


def test_rejects_encrypted_pdf_without_extracting_pages() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("synthetic-password")
    output = BytesIO()
    writer.write(output)
    extractor = SafeDocumentExtractor(maximum_pages=500, maximum_characters=100)

    with pytest.raises(DocumentExtractionError) as raised:
        extractor.extract(output.getvalue(), ".pdf")

    assert raised.value.code is ExtractionFailureCode.ENCRYPTED_PDF


def test_extracts_text_and_preserves_pdf_page_number() -> None:
    extractor = SafeDocumentExtractor(maximum_pages=500, maximum_characters=100)

    segments = extractor.extract(textual_pdf(), ".pdf")

    assert len(segments) == 1
    assert segments[0].page_number == 1
    assert segments[0].content == "Synthetic"


def test_rejects_pdf_without_text_layer() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    output = BytesIO()
    writer.write(output)
    extractor = SafeDocumentExtractor(maximum_pages=500, maximum_characters=100)

    with pytest.raises(DocumentExtractionError) as raised:
        extractor.extract(output.getvalue(), ".pdf")

    assert raised.value.code is ExtractionFailureCode.NO_EXTRACTABLE_TEXT


def test_rejects_pdf_above_page_limit() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=100, height=100)
    output = BytesIO()
    writer.write(output)
    extractor = SafeDocumentExtractor(maximum_pages=1, maximum_characters=100)

    with pytest.raises(DocumentExtractionError) as raised:
        extractor.extract(output.getvalue(), ".pdf")

    assert raised.value.code is ExtractionFailureCode.PAGE_LIMIT_EXCEEDED
