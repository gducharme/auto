"""create posts table

Revision ID: 0001_create_posts
Revises: 
Create Date: 2025-07-14
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_posts'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'posts',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('title', sa.Text()),
        sa.Column('link', sa.Text()),
        sa.Column('summary', sa.Text()),
        sa.Column('published', sa.Text()),
    )

def downgrade() -> None:
    op.drop_table('posts')
