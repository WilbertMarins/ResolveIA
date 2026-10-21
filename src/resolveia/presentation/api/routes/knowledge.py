"""Knowledge-base HTTP routes."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from resolveia.application.exceptions import (
    InvalidKnowledgeFileError,
    KnowledgeFileTooLargeError,
    KnowledgeDocumentNotFoundError,
    KnowledgeUploadUnavailableError,
)
from resolveia.application.use_cases import (
    MAX_FILE_SIZE_BYTES,
    GetKnowledgeDocument,
    UploadKnowledgeDocument,
    UploadKnowledgeDocumentCommand,
)
from resolveia.domain.knowledge import (
    DocumentType,
    KnowledgeDocumentValidationError,
)
from resolveia.presentation.api.dependencies import (
    get_get_knowledge_document,
    get_upload_knowledge_document,
)
from resolveia.presentation.api.schemas import (
    ExtractionSummaryResponse,
    KnowledgeDocumentDetailsResponse,
    KnowledgeDocumentResponse,
)

router = APIRouter(prefix="/knowledge/documents", tags=["knowledge"])


@router.get("/{document_id}", response_model=KnowledgeDocumentDetailsResponse)
async def get_knowledge_document(
    document_id: UUID,
    use_case: Annotated[GetKnowledgeDocument, Depends(get_get_knowledge_document)],
) -> KnowledgeDocumentDetailsResponse:
    """Return public metadata and the current extraction result."""
    try:
        details = await use_case.execute(document_id)
    except KnowledgeDocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document not found",
        ) from error

    document = details.document
    extraction = (
        ExtractionSummaryResponse.model_validate(details.extraction)
        if details.extraction is not None
        else None
    )
    return KnowledgeDocumentDetailsResponse(
        id=document.id,
        original_filename=document.original_filename,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        checksum_sha256=document.checksum_sha256,
        product=document.product,
        product_version=document.product_version,
        document_version=document.document_version,
        document_type=document.document_type,
        language=document.language,
        valid_until=document.valid_until,
        status=document.status,
        failure_reason=document.failure_reason,
        extraction=extraction,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.post(
    "",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_knowledge_document(
    file: Annotated[UploadFile, File()],
    product: Annotated[str, Form(min_length=1, max_length=100)],
    document_version: Annotated[str, Form(min_length=1, max_length=50)],
    document_type: Annotated[DocumentType, Form()],
    language: Annotated[str, Form(min_length=1, max_length=35)],
    use_case: Annotated[UploadKnowledgeDocument, Depends(get_upload_knowledge_document)],
    product_version: Annotated[str | None, Form(min_length=1, max_length=50)] = None,
    valid_until: Annotated[date | None, Form()] = None,
) -> KnowledgeDocumentResponse:
    """Store an original source document and register its metadata."""
    try:
        content = await file.read(MAX_FILE_SIZE_BYTES + 1)
    finally:
        await file.close()

    try:
        document = await use_case.execute(
            UploadKnowledgeDocumentCommand(
                original_filename=file.filename or "",
                content_type=file.content_type or "",
                content=content,
                product=product,
                product_version=product_version,
                document_version=document_version,
                document_type=document_type,
                language=language,
                valid_until=valid_until,
            )
        )
    except KnowledgeFileTooLargeError as error:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File exceeds the 10 MiB limit",
        ) from error
    except InvalidKnowledgeFileError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except KnowledgeDocumentValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except KnowledgeUploadUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Object storage is unavailable",
        ) from error

    return KnowledgeDocumentResponse.model_validate(document)
