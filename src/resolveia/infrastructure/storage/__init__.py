"""S3-compatible object-storage adapters."""

from resolveia.infrastructure.storage.s3 import (
    S3ObjectStorage,
    S3ReadinessCheck,
    create_s3_client,
)

__all__ = ["S3ObjectStorage", "S3ReadinessCheck", "create_s3_client"]
