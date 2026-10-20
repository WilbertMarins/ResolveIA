"""Persistence boundary for knowledge documents."""

from typing import Protocol

from resolveia.domain.knowledge import KnowledgeDocument


class KnowledgeDocumentRepository(Protocol):
    """Persist knowledge-document metadata without exposing a database API."""

    async def add(self, document: KnowledgeDocument) -> None:
        """Store a new knowledge document."""
        ...

    async def update(self, document: KnowledgeDocument) -> None:
        """Persist a lifecycle transition for an existing document."""
        ...
