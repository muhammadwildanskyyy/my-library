"""make file_url not null in books

Revision ID: a2f8c91d3e57
Revises: 91e3759ea16c
Create Date: 2026-06-11 19:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2f8c91d3e57'
down_revision: Union[str, None] = '91e3759ea16c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Fill any existing NULL values with a placeholder
    # (prevents ALTER COLUMN from failing on existing rows)
    op.execute("UPDATE books SET file_url = '' WHERE file_url IS NULL")

    # Step 2: Alter the column to NOT NULL
    op.alter_column(
        'books',
        'file_url',
        existing_type=sa.String(length=1000),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'books',
        'file_url',
        existing_type=sa.String(length=1000),
        nullable=True,
    )
