"""Integration tests for the SeaweedFS S3-compatible adapter."""

import asyncio

from resolveia.application.ports import ObjectToStore
from resolveia.infrastructure.config import get_settings
from resolveia.infrastructure.storage import (
    S3ObjectStorage,
    S3ReadinessCheck,
    create_s3_client,
)

OBJECT_KEY = "integration-tests/source-document.txt"


async def exercise_object_storage() -> None:
    settings = get_settings()
    client = create_s3_client(settings)
    storage = S3ObjectStorage(
        client,
        settings.object_storage_operation_timeout_seconds,
    )
    try:
        await storage.put(
            ObjectToStore(
                bucket=settings.object_storage_bucket,
                key=OBJECT_KEY,
                content=b"synthetic integration document",
                content_type="text/plain",
                metadata={"document-id": "integration-test", "sha256": "a" * 64},
            )
        )
        response = await asyncio.to_thread(
            client.head_object,
            Bucket=settings.object_storage_bucket,
            Key=OBJECT_KEY,
        )
        assert response["ContentType"] == "text/plain"
        assert response["Metadata"]["document-id"] == "integration-test"
        assert (
            await storage.get(
                settings.object_storage_bucket,
                OBJECT_KEY,
                1024,
            )
            == b"synthetic integration document"
        )

        readiness = S3ReadinessCheck(
            client,
            settings.object_storage_bucket,
            settings.object_storage_health_timeout_seconds,
        )
        assert await readiness.check() is True
    finally:
        await asyncio.to_thread(
            client.delete_object,
            Bucket=settings.object_storage_bucket,
            Key=OBJECT_KEY,
        )
        client.close()


def test_uploads_object_and_reports_bucket_as_ready() -> None:
    asyncio.run(exercise_object_storage())
