"""Dependency construction for short-lived worker and dispatcher operations."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from resolveia.application.use_cases.process_document_extraction import (
    ProcessDocumentExtraction,
)
from resolveia.infrastructure.config import Settings
from resolveia.infrastructure.database import (
    PostgresExtractionRepository,
    create_database,
)
from resolveia.infrastructure.extraction import SafeDocumentExtractor
from resolveia.infrastructure.storage import S3ObjectStorage, create_s3_client


@asynccontextmanager
async def extraction_use_case(
    settings: Settings,
) -> AsyncIterator[ProcessDocumentExtraction]:
    """Build isolated task dependencies and release their resources."""
    engine, session_factory = create_database(settings.database_url.get_secret_value())
    s3_client = create_s3_client(settings)
    try:
        async with session_factory() as session:
            yield ProcessDocumentExtraction(
                PostgresExtractionRepository(session),
                S3ObjectStorage(
                    s3_client,
                    settings.object_storage_operation_timeout_seconds,
                ),
                SafeDocumentExtractor(
                    settings.extraction_maximum_pages,
                    settings.extraction_maximum_characters,
                ),
                settings.extraction_lease_seconds,
            )
    finally:
        s3_client.close()
        await engine.dispose()
