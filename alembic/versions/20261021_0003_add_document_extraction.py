"""Add asynchronous document extraction persistence.

Revision ID: 20261021_0003
Revises: 20261019_0002
Create Date: 2026-10-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261021_0003"
down_revision: str | Sequence[str] | None = "20261019_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add extraction state, normalized segments, and durable outbox events."""
    op.add_column(
        "knowledge_documents",
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "knowledge_documents",
        sa.Column("processing_lease_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "knowledge_documents",
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "knowledge_documents",
        sa.Column(
            "extraction_attempts",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )

    op.create_table(
        "knowledge_extracted_segments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("character_count", sa.Integer(), nullable=False),
        sa.Column("content_checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("ordinal >= 0", name="ck_extracted_segments_ordinal"),
        sa.CheckConstraint(
            "page_number IS NULL OR page_number > 0",
            name="ck_extracted_segments_page_number",
        ),
        sa.CheckConstraint(
            "character_count > 0",
            name="ck_extracted_segments_character_count",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["knowledge_documents.id"],
            name="fk_extracted_segments_document_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_extracted_segments"),
        sa.UniqueConstraint(
            "document_id",
            "ordinal",
            name="uq_extracted_segments_document_ordinal",
        ),
    )
    op.create_index(
        "uq_extracted_segments_document_page",
        "knowledge_extracted_segments",
        ["document_id", "page_number"],
        unique=True,
        postgresql_where=sa.text("page_number IS NOT NULL"),
    )

    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("publish_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_failure_reason", sa.String(length=100), nullable=True),
        sa.CheckConstraint("publish_attempts >= 0", name="ck_outbox_publish_attempts"),
        sa.PrimaryKeyConstraint("id", name="pk_outbox_events"),
    )
    op.create_index(
        "ix_outbox_events_unpublished",
        "outbox_events",
        ["occurred_at"],
        unique=False,
        postgresql_where=sa.text("published_at IS NULL"),
    )


def downgrade() -> None:
    """Remove asynchronous extraction persistence."""
    op.drop_index("ix_outbox_events_unpublished", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_index(
        "uq_extracted_segments_document_page",
        table_name="knowledge_extracted_segments",
    )
    op.drop_table("knowledge_extracted_segments")
    op.drop_column("knowledge_documents", "extraction_attempts")
    op.drop_column("knowledge_documents", "extracted_at")
    op.drop_column("knowledge_documents", "processing_lease_until")
    op.drop_column("knowledge_documents", "processing_started_at")
