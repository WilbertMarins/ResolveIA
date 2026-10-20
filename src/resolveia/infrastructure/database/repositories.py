"""PostgreSQL repository adapters."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from resolveia.domain.knowledge import KnowledgeDocument
from resolveia.domain.tickets import Ticket
from resolveia.infrastructure.database.models import KnowledgeDocumentModel, TicketModel


class PostgresTicketRepository:
    """Persist tickets with a request-scoped SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, ticket: Ticket) -> None:
        """Store and commit a new ticket."""
        self._session.add(TicketModel.from_domain(ticket))
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def get(self, ticket_id: UUID) -> Ticket | None:
        """Return a domain ticket by identifier or None."""
        model = await self._session.get(TicketModel, ticket_id)
        return model.to_domain() if model is not None else None


class PostgresKnowledgeDocumentRepository:
    """Persist knowledge-document metadata with a request-scoped session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, document: KnowledgeDocument) -> None:
        """Store and commit the initial upload state."""
        self._session.add(KnowledgeDocumentModel.from_domain(document))
        await self._commit()

    async def update(self, document: KnowledgeDocument) -> None:
        """Merge and commit a document lifecycle transition."""
        await self._session.merge(KnowledgeDocumentModel.from_domain(document))
        await self._commit()

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
