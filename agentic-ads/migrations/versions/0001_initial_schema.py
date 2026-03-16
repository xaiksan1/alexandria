"""Initial schema: bid_cache, bid_history, sponsors

Revision ID: 0001
Revises:
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bid_cache",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("context_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("vertical", sa.String(32), nullable=False),
        sa.Column("encrypted_response", sa.LargeBinary, nullable=False),
        sa.Column("hit_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("win_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_hit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "bid_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("bid_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("context_hash", sa.String(64), nullable=False),
        sa.Column("vertical", sa.String(32), nullable=False),
        sa.Column("bid_amount", sa.Numeric(12, 6), nullable=False),
        sa.Column("w1", sa.Numeric(6, 4), nullable=False, server_default="0.7"),
        sa.Column("w2", sa.Numeric(6, 4), nullable=False, server_default="0.3"),
        sa.Column("won", sa.Boolean, nullable=False, server_default="FALSE"),
        sa.Column(
            "payment_confirmed", sa.Boolean, nullable=False, server_default="FALSE"
        ),
        sa.Column(
            "revenue_credited", sa.Boolean, nullable=False, server_default="FALSE"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "sponsors",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("vertical", sa.String(32), nullable=False),
        sa.Column("sponsor_name", sa.String(128), nullable=False),
        sa.Column("cta_type", sa.String(32), nullable=False),
        sa.Column("budget_remaining", sa.Numeric(14, 6), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean, nullable=False, server_default="TRUE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("sponsors")
    op.drop_table("bid_history")
    op.drop_table("bid_cache")
