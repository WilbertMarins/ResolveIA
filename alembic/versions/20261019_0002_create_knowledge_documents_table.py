"""Create the knowledge documents table.

Revision ID: 20261019_0002
Revises: 20261019_0001
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261019_0002"
down_revision: str | Sequence[str] | None = "20261019_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create metadata storage for source knowledge documents."""
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("extension", sa.String(length=10), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("product", sa.String(length=100), nullable=False),
        sa.Column("product_version", sa.String(length=50), nullable=True),
        sa.Column("document_version", sa.String(length=50), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("language", sa.String(length=35), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("storage_bucket", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("failure_reason", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("size_bytes > 0", name="ck_knowledge_documents_size_positive"),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_documents"),
        sa.UniqueConstraint("storage_key", name="uq_knowledge_documents_storage_key"),
    )


def downgrade() -> None:
    """Remove knowledge-document metadata storage."""
    op.drop_table("knowledge_documents")
