"""FastAPI application factory and default ASGI application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from resolveia.application.ports import (
    KnowledgeDocumentRepository,
    ObjectStorage,
    ReadinessCheck,
    TicketRepository,
)
from resolveia.infrastructure.config import Settings, get_settings
from resolveia.infrastructure.database import create_database
from resolveia.infrastructure.health import PostgresReadinessCheck, StaticReadinessCheck
from resolveia.infrastructure.storage import (
    S3ObjectStorage,
    S3ReadinessCheck,
    create_s3_client,
)
from resolveia.presentation.api.routes.health import router as health_router
from resolveia.presentation.api.routes.knowledge import router as knowledge_router
from resolveia.presentation.api.routes.tickets import router as tickets_router


def create_app(
    repository: TicketRepository | None = None,
    knowledge_document_repository: KnowledgeDocumentRepository | None = None,
    object_storage: ObjectStorage | None = None,
    settings: Settings | None = None,
    readiness_check: ReadinessCheck | None = None,
    object_storage_readiness_check: ReadinessCheck | None = None,
) -> FastAPI:
    """Create an isolated API instance with replaceable infrastructure."""

    @asynccontextmanager
    async def lifespan(api: FastAPI) -> AsyncIterator[None]:
        if repository is not None:
            api.state.readiness_checks = {
                "database": (
                    readiness_check
                    if readiness_check is not None
                    else StaticReadinessCheck(True)
                ),
                "object_storage": (
                    object_storage_readiness_check
                    if object_storage_readiness_check is not None
                    else StaticReadinessCheck(True)
                ),
            }
            yield
            return

        resolved_settings = settings if settings is not None else get_settings()
        engine, session_factory = create_database(
            resolved_settings.database_url.get_secret_value()
        )
        s3_client = create_s3_client(resolved_settings)
        api.state.session_factory = session_factory
        api.state.object_storage = (
            object_storage
            if object_storage is not None
            else S3ObjectStorage(
                s3_client,
                resolved_settings.object_storage_operation_timeout_seconds,
            )
        )
        api.state.object_storage_bucket = resolved_settings.object_storage_bucket
        api.state.readiness_checks = {
            "database": (
                readiness_check
                if readiness_check is not None
                else PostgresReadinessCheck(
                    session_factory,
                    resolved_settings.database_health_timeout_seconds,
                )
            ),
            "object_storage": (
                object_storage_readiness_check
                if object_storage_readiness_check is not None
                else S3ReadinessCheck(
                    s3_client,
                    resolved_settings.object_storage_bucket,
                    resolved_settings.object_storage_health_timeout_seconds,
                )
            ),
        }
        try:
            yield
        finally:
            s3_client.close()
            await engine.dispose()

    api = FastAPI(
        title="ResolveIA API",
        description="Multi-agent technical support for a fictional payment API.",
        version="0.1.0",
        lifespan=lifespan,
    )
    api.state.ticket_repository_override = repository
    api.state.knowledge_document_repository_override = knowledge_document_repository
    api.state.object_storage = object_storage
    api.state.object_storage_bucket = (
        settings.object_storage_bucket if settings is not None else "resolveia-knowledge"
    )
    api.include_router(health_router)
    api.include_router(knowledge_router, prefix="/api/v1")
    api.include_router(tickets_router, prefix="/api/v1")
    return api


app = create_app()
