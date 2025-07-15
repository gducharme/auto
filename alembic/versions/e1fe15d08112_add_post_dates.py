"""add created_at and updated_at columns to posts

Revision ID: e1fe15d08112
Revises: 468d8314d708
Create Date: 2025-07-15 12:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e1fe15d08112"
down_revision: Union[str, Sequence[str], None] = "955b42e04385"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("posts", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("posts", sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("posts", "updated_at")
    op.drop_column("posts", "created_at")
