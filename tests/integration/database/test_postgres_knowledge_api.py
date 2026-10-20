"""End-to-end persistence test for knowledge-document upload wiring."""

import asyncio
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import delete

from resolveia.infrastructure.config import get_settings
from resolveia.infrastructure.database import create_database
from resolveia.infrastructure.database.models import KnowledgeDocumentModel
from resolveia.infrastructure.storage import create_s3_client
from resolveia.presentation.api.app import create_app

PAYLOAD = {
    "product": "payments-api",
    "product_version": "2.4",
    "document_version": "2026.10",
    "document_type": "runbook",
    "language": "pt-BR",
    "valid_until": "2027-10-31",
}


async def assert_persisted_and_remove(document_id: UUID) -> None:
    """Verify both resources and remove only this test's artifacts."""
    settings = get_settings()
    engine, session_factory = create_database(settings.database_url.get_secret_value())
    client = create_s3_client(settings)
    try:
        async with session_factory() as session:
            model = await session.get(KnowledgeDocumentModel, document_id)
            assert model is not None
            assert model.status == "pending_ingestion"
            response = await asyncio.to_thread(
                client.head_object,
                Bucket=model.storage_bucket,
                Key=model.storage_key,
            )
            assert response["ContentLength"] == len(b"# Synthetic integration runbook")
            await asyncio.to_thread(
                client.delete_object,
                Bucket=model.storage_bucket,
                Key=model.storage_key,
            )
            await session.execute(
                delete(KnowledgeDocumentModel).where(
                    KnowledgeDocumentModel.id == document_id
                )
            )
            await session.commit()
    finally:
        client.close()
        await engine.dispose()


def test_upload_persists_metadata_and_original_object() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/knowledge/documents",
            data=PAYLOAD,
            files={
                "file": (
                    "payments-api.md",
                    b"# Synthetic integration runbook",
                    "text/markdown",
                )
            },
        )

    assert response.status_code == 201
    document_id = UUID(response.json()["id"])
    asyncio.run(assert_persisted_and_remove(document_id))
