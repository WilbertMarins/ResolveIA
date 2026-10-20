"""Create the tickets table.

Revision ID: 20261019_0001
Revises:
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261019_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the initial ticket persistence schema."""
    op.create_table(
        "tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=5_000), nullable=False),
        sa.Column("product", sa.String(length=100), nullable=False),
        sa.Column("product_version", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tickets"),
    )


def downgrade() -> None:
    """Remove the initial ticket persistence schema."""
    op.drop_table("tickets")
