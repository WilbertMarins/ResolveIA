"""FastAPI dependency providers."""

from collections.abc import AsyncIterator, Mapping
from typing import Annotated, cast

from fastapi import Depends, Request

from resolveia.application.ports import (
    KnowledgeDocumentRepository,
    ObjectStorage,
    ReadinessCheck,
    TicketRepository,
)
from resolveia.application.use_cases import CreateTicket, GetTicket, UploadKnowledgeDocument
from resolveia.infrastructure.database import (
    PostgresKnowledgeDocumentRepository,
    PostgresTicketRepository,
    SessionFactory,
)


def get_readiness_checks(request: Request) -> Mapping[str, ReadinessCheck]:
    """Return the named readiness checks configured for this application."""
    return cast(Mapping[str, ReadinessCheck], request.app.state.readiness_checks)


async def get_ticket_repository(request: Request) -> AsyncIterator[TicketRepository]:
    """Provide an injected repository or a request-scoped PostgreSQL adapter."""
    repository = cast(
        TicketRepository | None,
        request.app.state.ticket_repository_override,
    )
    if repository is not None:
        yield repository
        return

    session_factory = cast(SessionFactory, request.app.state.session_factory)
    async with session_factory() as session:
        yield PostgresTicketRepository(session)


async def get_knowledge_document_repository(
    request: Request,
) -> AsyncIterator[KnowledgeDocumentRepository]:
    """Provide an injected repository or a request-scoped PostgreSQL adapter."""
    repository = cast(
        KnowledgeDocumentRepository | None,
        request.app.state.knowledge_document_repository_override,
    )
    if repository is not None:
        yield repository
        return

    session_factory = cast(SessionFactory, request.app.state.session_factory)
    async with session_factory() as session:
        yield PostgresKnowledgeDocumentRepository(session)


def get_object_storage(request: Request) -> ObjectStorage:
    """Return the configured object-storage adapter."""
    return cast(ObjectStorage, request.app.state.object_storage)


def get_create_ticket(
    repository: Annotated[TicketRepository, Depends(get_ticket_repository)],
) -> CreateTicket:
    """Build the create-ticket use case with request-scoped dependencies."""
    return CreateTicket(repository)


def get_get_ticket(
    repository: Annotated[TicketRepository, Depends(get_ticket_repository)],
) -> GetTicket:
    """Build the get-ticket use case with request-scoped dependencies."""
    return GetTicket(repository)


def get_upload_knowledge_document(
    repository: Annotated[
        KnowledgeDocumentRepository,
        Depends(get_knowledge_document_repository),
    ],
    object_storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    request: Request,
) -> UploadKnowledgeDocument:
    """Build the upload use case with request-scoped dependencies."""
    bucket = cast(str, request.app.state.object_storage_bucket)
    return UploadKnowledgeDocument(repository, object_storage, bucket)
