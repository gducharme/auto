"""add post_previews table

Revision ID: 0002
Revises: 0001
Create Date: 2025-07-15 00:00:01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "post_previews",
        sa.Column("post_id", sa.String(), sa.ForeignKey("posts.id"), primary_key=True),
        sa.Column("network", sa.String(), primary_key=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    op.drop_table("post_previews")
