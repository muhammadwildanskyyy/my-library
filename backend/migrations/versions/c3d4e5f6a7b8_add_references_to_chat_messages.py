"""add references to chat_messages

Revision ID: c3d4e5f6a7b8
Revises: 303c6b28862d
Create Date: 2026-06-11 13:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'a2f8c91d3e57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add JSONB column to store citation references per AI message
    # Nullable because user messages never have references
    op.add_column(
        'chat_messages',
        sa.Column(
            'references',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=None,
        )
    )


def downgrade() -> None:
    op.drop_column('chat_messages', 'references')
