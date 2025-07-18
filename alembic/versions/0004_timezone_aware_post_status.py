"""Ensure stored scheduled_at values have timezone info

Revision ID: 0004
Revises: 0003
Create Date: 2025-07-19 00:00:00
"""

from typing import Sequence, Union
from datetime import timezone

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    post_status = sa.table(
        "post_status",
        sa.column("post_id", sa.String()),
        sa.column("network", sa.String()),
        sa.column("scheduled_at", sa.DateTime()),
    )

    rows = conn.execute(
        sa.select(post_status.c.post_id, post_status.c.network, post_status.c.scheduled_at)
    ).fetchall()

    for pid, net, ts in rows:
        if ts is not None and getattr(ts, "tzinfo", None) is None:
            aware = ts.replace(tzinfo=timezone.utc)
            conn.execute(
                post_status.update()
                .where(
                    post_status.c.post_id == pid,
                    post_status.c.network == net,
                )
                .values(scheduled_at=aware)
            )


def downgrade() -> None:
    pass

