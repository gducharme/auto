"""create posts table

Revision ID: 468d8314d708
Revises: c417e4f8437a
Create Date: 2025-07-14 17:49:36.623291

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '468d8314d708'
down_revision: Union[str, Sequence[str], None] = 'c417e4f8437a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.create_table(
        'posts',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('link', sa.String(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('published', sa.String(), nullable=True),
    )
    # If you want an explicit index on title or link, you can add:
    # op.create_index('ix_posts_title', 'posts', ['title'])


def downgrade():
    op.drop_table('posts')
