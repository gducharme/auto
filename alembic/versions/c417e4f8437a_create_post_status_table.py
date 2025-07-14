"""create post_status table

Revision ID: c417e4f8437a
Revises: 
Create Date: 2025-07-14 17:44:04.131015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c417e4f8437a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.create_table(
        'post_status',
        sa.Column('post_id', sa.String(), nullable=False),
        sa.Column('network', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),
        sa.PrimaryKeyConstraint('post_id', 'network'),
    )
    # optionally: add a foreign key if you like
    # op.create_foreign_key(
    #     'fk_post', 'post_status', 'posts', ['post_id'], ['id']
    # )


def downgrade():
    op.drop_table('post_status')
