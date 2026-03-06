"""add instagram pipeline tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-05 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, Sequence[str], None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "instagram_pipeline_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.String(), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("network", sa.String(), nullable=False, server_default="instagram"),
        sa.Column("pipeline_version", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("selected_concept_id", sa.Integer(), nullable=True),
        sa.Column("score_summary", sa.Text(), nullable=True),
        sa.Column("publish_payload", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "post_id",
            "network",
            "pipeline_version",
            name="uq_instagram_pipeline_run_key",
        ),
    )

    op.create_table(
        "instagram_pipeline_concepts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("instagram_pipeline_runs.id"),
            nullable=False,
        ),
        sa.Column("concept_key", sa.String(), nullable=False),
        sa.Column("concept_payload", sa.Text(), nullable=False),
        sa.Column("score_total", sa.Float(), nullable=True),
        sa.Column("score_breakdown", sa.Text(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "run_id",
            "concept_key",
            name="uq_instagram_pipeline_concept_key",
        ),
    )

    op.create_table(
        "instagram_pipeline_assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("instagram_pipeline_runs.id"),
            nullable=False,
        ),
        sa.Column(
            "concept_id",
            sa.Integer(),
            sa.ForeignKey("instagram_pipeline_concepts.id"),
            nullable=True,
        ),
        sa.Column("asset_key", sa.String(), nullable=False),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("asset_uri", sa.Text(), nullable=True),
        sa.Column("asset_metadata", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "run_id",
            "asset_key",
            name="uq_instagram_pipeline_asset_key",
        ),
    )


def downgrade() -> None:
    op.drop_table("instagram_pipeline_assets")
    op.drop_table("instagram_pipeline_concepts")
    op.drop_table("instagram_pipeline_runs")
