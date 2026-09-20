"""Add revoked_tokens table for logout support

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-20

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(length=64), primary_key=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("revoked_tokens")
