"""add content column to posts

Revision ID: 0005
Revises: 0004
Create Date: 2025-08-01 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("content", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("posts", "content")
