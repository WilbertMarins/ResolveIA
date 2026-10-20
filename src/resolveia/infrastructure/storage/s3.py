"""S3-compatible adapter used with SeaweedFS."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from resolveia.application.ports import ObjectStorageError, ObjectToStore
from resolveia.infrastructure.config import Settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
else:
    S3Client = Any


def create_s3_client(settings: Settings) -> S3Client:
    """Build a path-style S3 client without performing network I/O."""
    return boto3.client(
        "s3",
        endpoint_url=settings.object_storage_endpoint_url,
        aws_access_key_id=settings.object_storage_access_key.get_secret_value(),
        aws_secret_access_key=settings.object_storage_secret_key.get_secret_value(),
        region_name=settings.object_storage_region,
        config=Config(
            connect_timeout=settings.object_storage_operation_timeout_seconds,
            read_timeout=settings.object_storage_operation_timeout_seconds,
            retries={"max_attempts": 2, "mode": "standard"},
            s3={"addressing_style": "path"},
        ),
    )


class S3ObjectStorage:
    """Upload objects through an S3-compatible client off the event loop."""

    def __init__(self, client: S3Client, timeout_seconds: float) -> None:
        self._client = client
        self._timeout_seconds = timeout_seconds

    async def put(self, item: ObjectToStore) -> None:
        """Upload an object and map provider errors to the application contract."""
        try:
            async with asyncio.timeout(self._timeout_seconds):
                await asyncio.to_thread(
                    self._client.put_object,
                    Bucket=item.bucket,
                    Key=item.key,
                    Body=item.content,
                    ContentType=item.content_type,
                    Metadata=item.metadata,
                )
        except (TimeoutError, OSError, BotoCoreError, ClientError) as error:
            raise ObjectStorageError("S3-compatible upload failed") from error


class S3ReadinessCheck:
    """Check whether the configured object-storage bucket is reachable."""

    def __init__(self, client: S3Client, bucket: str, timeout_seconds: float) -> None:
        self._client = client
        self._bucket = bucket
        self._timeout_seconds = timeout_seconds

    async def check(self) -> bool:
        """Return false for connectivity, authorization, and timeout failures."""
        try:
            async with asyncio.timeout(self._timeout_seconds):
                await asyncio.to_thread(self._client.head_bucket, Bucket=self._bucket)
        except (TimeoutError, OSError, BotoCoreError, ClientError):
            return False
        return True
