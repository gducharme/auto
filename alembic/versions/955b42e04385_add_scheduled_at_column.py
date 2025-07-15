"""add scheduled_at column

Revision ID: 955b42e04385
Revises: 468d8314d708
Create Date: 2025-07-14 17:49:36
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '955b42e04385'
down_revision: Union[str, Sequence[str], None] = '468d8314d708'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.add_column('post_status', sa.Column('scheduled_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))


def downgrade():
    op.drop_column('post_status', 'scheduled_at')
