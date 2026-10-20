"""Object-storage boundary used by knowledge ingestion."""

from dataclasses import dataclass
from typing import Protocol


class ObjectStorageError(RuntimeError):
    """Raised when object storage cannot complete an operation."""


@dataclass(frozen=True, slots=True)
class ObjectToStore:
    """Provider-independent object upload data."""

    bucket: str
    key: str
    content: bytes
    content_type: str
    metadata: dict[str, str]


class ObjectStorage(Protocol):
    """Store immutable source objects behind a provider-neutral contract."""

    async def put(self, item: ObjectToStore) -> None:
        """Upload one object or raise ObjectStorageError."""
        ...
