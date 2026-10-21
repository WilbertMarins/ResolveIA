"""Relational models and explicit domain mappings."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from resolveia.domain.knowledge import (
    DocumentStatus,
    DocumentType,
    ExtractedSegment,
    KnowledgeDocument,
    OutboxEvent,
)
from resolveia.domain.tickets import Ticket, TicketStatus
from resolveia.infrastructure.database.base import Base


class TicketModel(Base):
    """Relational representation of a support ticket."""

    __tablename__ = "tickets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(5_000), nullable=False)
    product: Mapped[str] = mapped_column(String(100), nullable=False)
    product_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @classmethod
    def from_domain(cls, ticket: Ticket) -> "TicketModel":
        """Create a persistence model from a domain entity."""
        return cls(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            product=ticket.product,
            product_version=ticket.product_version,
            status=ticket.status.value,
            created_at=ticket.created_at,
        )

    def to_domain(self) -> Ticket:
        """Reconstruct a domain entity from persisted values."""
        return Ticket(
            id=self.id,
            title=self.title,
            description=self.description,
            product=self.product,
            product_version=self.product_version,
            status=TicketStatus(self.status),
            created_at=self.created_at,
        )


class KnowledgeDocumentModel(Base):
    """Relational representation of knowledge-document metadata."""

    __tablename__ = "knowledge_documents"
    __table_args__ = (
        CheckConstraint(
            "size_bytes > 0",
            name="ck_knowledge_documents_size_positive",
        ),
        UniqueConstraint(
            "storage_key",
            name="uq_knowledge_documents_storage_key",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extension: Mapped[str] = mapped_column(String(10), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    product: Mapped[str] = mapped_column(String(100), nullable=False)
    product_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    document_version: Mapped[str] = mapped_column(String(50), nullable=False)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    language: Mapped[str] = mapped_column(String(35), nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_lease_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    extracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    extraction_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    @classmethod
    def from_domain(cls, document: KnowledgeDocument) -> "KnowledgeDocumentModel":
        """Create a persistence model from a domain entity."""
        return cls(
            id=document.id,
            original_filename=document.original_filename,
            content_type=document.content_type,
            extension=document.extension,
            size_bytes=document.size_bytes,
            checksum_sha256=document.checksum_sha256,
            product=document.product,
            product_version=document.product_version,
            document_version=document.document_version,
            document_type=document.document_type.value,
            language=document.language,
            valid_until=document.valid_until,
            storage_bucket=document.storage_bucket,
            storage_key=document.storage_key,
            status=document.status.value,
            failure_reason=document.failure_reason,
            created_at=document.created_at,
            updated_at=document.updated_at,
            processing_started_at=document.processing_started_at,
            processing_lease_until=document.processing_lease_until,
            extracted_at=document.extracted_at,
            extraction_attempts=document.extraction_attempts,
        )

    def to_domain(self) -> KnowledgeDocument:
        """Reconstruct a domain entity from persisted values."""
        return KnowledgeDocument(
            id=self.id,
            original_filename=self.original_filename,
            content_type=self.content_type,
            extension=self.extension,
            size_bytes=self.size_bytes,
            checksum_sha256=self.checksum_sha256,
            product=self.product,
            product_version=self.product_version,
            document_version=self.document_version,
            document_type=DocumentType(self.document_type),
            language=self.language,
            valid_until=self.valid_until,
            storage_bucket=self.storage_bucket,
            storage_key=self.storage_key,
            status=DocumentStatus(self.status),
            failure_reason=self.failure_reason,
            created_at=self.created_at,
            updated_at=self.updated_at,
            processing_started_at=self.processing_started_at,
            processing_lease_until=self.processing_lease_until,
            extracted_at=self.extracted_at,
            extraction_attempts=self.extraction_attempts,
        )


class ExtractedSegmentModel(Base):
    """Relational representation of one normalized source unit."""

    __tablename__ = "knowledge_extracted_segments"
    __table_args__ = (
        CheckConstraint("ordinal >= 0", name="ck_extracted_segments_ordinal"),
        CheckConstraint(
            "page_number IS NULL OR page_number > 0",
            name="ck_extracted_segments_page_number",
        ),
        CheckConstraint(
            "character_count > 0",
            name="ck_extracted_segments_character_count",
        ),
        UniqueConstraint(
            "document_id",
            "ordinal",
            name="uq_extracted_segments_document_ordinal",
        ),
        Index(
            "uq_extracted_segments_document_page",
            "document_id",
            "page_number",
            unique=True,
            postgresql_where=text("page_number IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False)
    content_checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @classmethod
    def from_domain(cls, segment: ExtractedSegment) -> "ExtractedSegmentModel":
        return cls(
            id=segment.id,
            document_id=segment.document_id,
            ordinal=segment.ordinal,
            page_number=segment.page_number,
            content=segment.content,
            character_count=segment.character_count,
            content_checksum_sha256=segment.content_checksum_sha256,
            created_at=segment.created_at,
        )


class OutboxEventModel(Base):
    """Relational representation of a durable integration event."""

    __tablename__ = "outbox_events"
    __table_args__ = (
        CheckConstraint("publish_attempts >= 0", name="ck_outbox_publish_attempts"),
        Index(
            "ix_outbox_events_unpublished",
            "occurred_at",
            postgresql_where=text("published_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    payload: Mapped[dict[str, str | int]] = mapped_column(JSONB, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    publish_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    last_failure_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)

    @classmethod
    def from_domain(cls, event: OutboxEvent) -> "OutboxEventModel":
        return cls(
            id=event.id,
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            payload=event.payload,
            occurred_at=event.occurred_at,
            published_at=event.published_at,
            publish_attempts=event.publish_attempts,
            last_failure_reason=event.last_failure_reason,
        )

    def to_domain(self) -> OutboxEvent:
        return OutboxEvent(
            id=self.id,
            event_type=self.event_type,
            aggregate_id=self.aggregate_id,
            payload=self.payload,
            occurred_at=self.occurred_at,
            published_at=self.published_at,
            publish_attempts=self.publish_attempts,
            last_failure_reason=self.last_failure_reason,
        )
