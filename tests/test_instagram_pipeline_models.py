from __future__ import annotations

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from auto.db import SessionLocal
from auto.models import (
    InstagramPipelineAsset,
    InstagramPipelineConcept,
    InstagramPipelineRun,
    Post,
)


def test_instagram_pipeline_tables_exist_after_migration(test_db_engine):
    inspector = inspect(test_db_engine)
    tables = set(inspector.get_table_names())
    assert "instagram_pipeline_runs" in tables
    assert "instagram_pipeline_concepts" in tables
    assert "instagram_pipeline_assets" in tables


def test_instagram_pipeline_run_unique_key_constraint(test_db_engine):
    with SessionLocal() as session:
        session.add(
            Post(
                id="ig-post-1",
                title="IG Post",
                link="https://example.com/ig-post-1",
                summary="",
                published="",
            )
        )
        session.commit()

        session.add(
            InstagramPipelineRun(
                post_id="ig-post-1",
                network="instagram",
                pipeline_version="v1",
                status="pending",
            )
        )
        session.commit()

        session.add(
            InstagramPipelineRun(
                post_id="ig-post-1",
                network="instagram",
                pipeline_version="v1",
                status="pending",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_instagram_pipeline_concepts_and_assets_linkage(test_db_engine):
    with SessionLocal() as session:
        session.add(
            Post(
                id="ig-post-2",
                title="IG Post 2",
                link="https://example.com/ig-post-2",
                summary="",
                published="",
            )
        )
        session.commit()

        run = InstagramPipelineRun(
            post_id="ig-post-2",
            network="instagram",
            pipeline_version="v1",
            status="pending",
        )
        session.add(run)
        session.commit()

        concept = InstagramPipelineConcept(
            run_id=run.id,
            concept_key="c1",
            concept_payload='{"hook":"A visual hook"}',
            score_total=0.95,
            score_breakdown='{"visual":0.98,"engagement":0.92}',
            rank=1,
        )
        session.add(concept)
        session.commit()

        asset = InstagramPipelineAsset(
            run_id=run.id,
            concept_id=concept.id,
            asset_key="carousel-1",
            asset_type="carousel_slide",
            asset_uri="s3://bucket/asset-1.png",
            asset_metadata='{"width":1080,"height":1350}',
            status="rendered",
        )
        session.add(asset)
        session.commit()

        stored_asset = session.get(InstagramPipelineAsset, asset.id)
        assert stored_asset is not None
        assert stored_asset.run_id == run.id
        assert stored_asset.concept_id == concept.id
        assert stored_asset.status == "rendered"
