"""add langchain pgvector tables

Revision ID: b1a3f7e20c41
Revises: 9c62316ade80
Create Date: 2026-06-07 15:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b1a3f7e20c41'
down_revision: Union[str, None] = '9c62316ade80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use raw SQL with IF NOT EXISTS since langchain_postgres may have
    # already auto-created these tables on first app startup.

    # ── 1. langchain_pg_collection ────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS langchain_pg_collection (
            uuid UUID PRIMARY KEY,
            name VARCHAR NOT NULL UNIQUE,
            cmetadata JSONB
        )
    """)

    # ── 2. langchain_pg_embedding ─────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS langchain_pg_embedding (
            id VARCHAR PRIMARY KEY,
            collection_id UUID REFERENCES langchain_pg_collection(uuid) ON DELETE CASCADE,
            embedding BYTEA,
            document TEXT,
            cmetadata JSONB
        )
    """)

    # ── 3. Index on collection_id (skip if exists) ────────────────────────
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_langchain_pg_embedding_collection_id
        ON langchain_pg_embedding (collection_id)
    """)

    # ── 4. GIN index for PostgreSQL Full-Text Search ──────────────────────
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_langchain_pg_embedding_fts
        ON langchain_pg_embedding
        USING gin(to_tsvector('english', document))
    """)

    # ── 5. GIN index on cmetadata for JSONB containment (@>) filters ──────
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_langchain_pg_embedding_cmetadata
        ON langchain_pg_embedding
        USING gin(cmetadata jsonb_path_ops)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_langchain_pg_embedding_cmetadata")
    op.execute("DROP INDEX IF EXISTS ix_langchain_pg_embedding_fts")
    op.execute("DROP INDEX IF EXISTS ix_langchain_pg_embedding_collection_id")
    op.execute("DROP TABLE IF EXISTS langchain_pg_embedding")
    op.execute("DROP TABLE IF EXISTS langchain_pg_collection")
