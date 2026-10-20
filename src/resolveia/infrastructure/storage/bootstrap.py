"""Explicit, idempotent bucket bootstrap for local and CI environments."""

from botocore.exceptions import ClientError

from resolveia.infrastructure.config import get_settings
from resolveia.infrastructure.storage import create_s3_client


def main() -> None:
    """Create the configured bucket when it does not already exist."""
    settings = get_settings()
    client = create_s3_client(settings)
    bucket = settings.object_storage_bucket
    try:
        try:
            client.head_bucket(Bucket=bucket)
        except ClientError as error:
            status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status_code != 404:
                raise
            client.create_bucket(Bucket=bucket)
        print(f"Object-storage bucket is ready: {bucket}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
