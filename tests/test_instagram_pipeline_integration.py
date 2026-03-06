from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from auto.db import SessionLocal
from auto.models import (
    InstagramPipelineConcept,
    InstagramPipelineRun,
    Post,
    PostStatus,
    Task,
)
from auto.scheduler import process_pending
from auto.socials.registry import get_registry, reset_registry


class FakeInstagramPlugin:
    network = "instagram"

    def __init__(self) -> None:
        self.posts: list[tuple[str, str]] = []

    async def post(self, text: str, visibility: str = "unlisted") -> None:
        self.posts.append((text, visibility))


def _run_pending() -> None:
    asyncio.run(process_pending())


def test_instagram_pipeline_auto_publish_happy_path(test_db_engine, monkeypatch):
    reset_registry()
    plugin = FakeInstagramPlugin()
    get_registry().register(plugin)

    monkeypatch.setenv("INSTAGRAM_PIPELINE_ENABLED", "1")
    monkeypatch.setenv("INSTAGRAM_PIPELINE_QUALITY_THRESHOLD", "0.1")

    with SessionLocal() as session:
        session.add(
            Post(
                id="ig-pipeline-1",
                title="Visual Pipeline",
                link="https://example.com/visual-pipeline",
                summary="Short visual-first summary",
                published="",
            )
        )
        session.add(
            Task(
                type="instagram_pipeline_run",
                payload=json.dumps(
                    {
                        "post_id": "ig-pipeline-1",
                        "network": "instagram",
                        "pipeline_version": "v1",
                        "auto_publish": True,
                    }
                ),
                scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
        )
        session.commit()

    _run_pending()

    with SessionLocal() as session:
        run = (
            session.query(InstagramPipelineRun)
            .filter(
                InstagramPipelineRun.post_id == "ig-pipeline-1",
                InstagramPipelineRun.network == "instagram",
                InstagramPipelineRun.pipeline_version == "v1",
            )
            .first()
        )
        assert run is not None
        assert run.status == "published"
        assert run.selected_concept_id is not None
        assert run.publish_payload is not None
        payload = json.loads(run.publish_payload)
        assert payload["adapter_version"] == "ig-adapter-v1"
        assert payload["publish_format"] == "carousel"
        assert len(payload["media_items"]) >= 1

        concepts = (
            session.query(InstagramPipelineConcept)
            .filter(InstagramPipelineConcept.run_id == run.id)
            .order_by(InstagramPipelineConcept.rank.asc())
            .all()
        )
        assert len(concepts) == 3

        status = session.get(
            PostStatus, {"post_id": "ig-pipeline-1", "network": "instagram"}
        )
        assert status is not None
        assert status.status == "published"

    assert len(plugin.posts) == 1
    posted_text, visibility = plugin.posts[0]
    assert posted_text
    assert "#visual" in posted_text or "#pipeline" in posted_text
    assert visibility == "unlisted"


def test_instagram_pipeline_respects_quality_threshold(test_db_engine, monkeypatch):
    reset_registry()
    plugin = FakeInstagramPlugin()
    get_registry().register(plugin)

    monkeypatch.setenv("INSTAGRAM_PIPELINE_ENABLED", "1")
    monkeypatch.setenv("INSTAGRAM_PIPELINE_QUALITY_THRESHOLD", "0.99")

    with SessionLocal() as session:
        session.add(
            Post(
                id="ig-pipeline-2",
                title="Threshold Check",
                link="https://example.com/threshold",
                summary="",
                published="",
            )
        )
        session.add(
            Task(
                type="instagram_pipeline_run",
                payload=json.dumps(
                    {
                        "post_id": "ig-pipeline-2",
                        "network": "instagram",
                        "pipeline_version": "v1",
                        "auto_publish": True,
                    }
                ),
                scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
        )
        session.commit()

    _run_pending()

    with SessionLocal() as session:
        run = (
            session.query(InstagramPipelineRun)
            .filter(InstagramPipelineRun.post_id == "ig-pipeline-2")
            .first()
        )
        assert run is not None
        assert run.status == "needs_review"
        assert run.last_error == "quality threshold not met"

        status = session.get(
            PostStatus, {"post_id": "ig-pipeline-2", "network": "instagram"}
        )
        assert status is None

    assert plugin.posts == []


def test_instagram_pipeline_kill_switch_disables_run(test_db_engine, monkeypatch):
    reset_registry()
    plugin = FakeInstagramPlugin()
    get_registry().register(plugin)

    monkeypatch.setenv("INSTAGRAM_PIPELINE_ENABLED", "0")

    with SessionLocal() as session:
        session.add(
            Post(
                id="ig-pipeline-3",
                title="Kill Switch",
                link="https://example.com/kill-switch",
                summary="",
                published="",
            )
        )
        session.add(
            Task(
                type="instagram_pipeline_run",
                payload=json.dumps(
                    {
                        "post_id": "ig-pipeline-3",
                        "network": "instagram",
                        "pipeline_version": "v1",
                        "auto_publish": True,
                    }
                ),
                scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
        )
        session.commit()

    _run_pending()

    with SessionLocal() as session:
        run = (
            session.query(InstagramPipelineRun)
            .filter(InstagramPipelineRun.post_id == "ig-pipeline-3")
            .first()
        )
        assert run is not None
        assert run.status == "disabled"

    assert plugin.posts == []


def test_instagram_pipeline_idempotent_publish_for_same_run_key(
    test_db_engine, monkeypatch
):
    reset_registry()
    plugin = FakeInstagramPlugin()
    get_registry().register(plugin)

    monkeypatch.setenv("INSTAGRAM_PIPELINE_ENABLED", "1")
    monkeypatch.setenv("INSTAGRAM_PIPELINE_QUALITY_THRESHOLD", "0.1")

    payload = json.dumps(
        {
            "post_id": "ig-pipeline-4",
            "network": "instagram",
            "pipeline_version": "v1",
            "auto_publish": True,
        }
    )

    with SessionLocal() as session:
        session.add(
            Post(
                id="ig-pipeline-4",
                title="Idempotent",
                link="https://example.com/idempotent",
                summary="",
                published="",
            )
        )
        session.add_all(
            [
                Task(
                    type="instagram_pipeline_run",
                    payload=payload,
                    scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=2),
                ),
                Task(
                    type="instagram_pipeline_run",
                    payload=payload,
                    scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
                ),
            ]
        )
        session.commit()

    _run_pending()

    with SessionLocal() as session:
        runs = (
            session.query(InstagramPipelineRun)
            .filter(InstagramPipelineRun.post_id == "ig-pipeline-4")
            .all()
        )
        assert len(runs) == 1
        assert runs[0].status == "published"

    assert len(plugin.posts) == 1


def test_instagram_pipeline_exports_artifacts_and_preview(test_db_engine, monkeypatch):
    reset_registry()
    plugin = FakeInstagramPlugin()
    get_registry().register(plugin)

    export_dir = Path("tmp/test-instagram-artifacts")
    monkeypatch.setenv("INSTAGRAM_PIPELINE_ENABLED", "1")
    monkeypatch.setenv("INSTAGRAM_PIPELINE_QUALITY_THRESHOLD", "0.1")
    monkeypatch.setenv("INSTAGRAM_PIPELINE_EXPORT_ENABLED", "1")
    monkeypatch.setenv("INSTAGRAM_PIPELINE_EXPORT_DIR", str(export_dir))

    with SessionLocal() as session:
        session.add(
            Post(
                id="ig-pipeline-5",
                title="Artifact Export",
                link="https://example.com/artifacts",
                summary="",
                published="",
            )
        )
        session.add(
            Task(
                type="instagram_pipeline_run",
                payload=json.dumps(
                    {
                        "post_id": "ig-pipeline-5",
                        "network": "instagram",
                        "pipeline_version": "v1",
                        "auto_publish": False,
                    }
                ),
                scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
        )
        session.commit()

    _run_pending()

    root = export_dir / "ig-pipeline-5" / "instagram" / "v1"
    run_dirs = sorted(
        p for p in root.iterdir() if p.is_dir() and p.name.startswith("run_")
    )
    assert run_dirs, "expected at least one run artifact directory"
    latest = run_dirs[-1]

    assert (latest / "run.json").exists()
    assert (latest / "concepts_ranked.json").exists()
    assert (latest / "publish_payload.json").exists()
    assert (latest / "preview.md").exists()
    assert (latest / "preview.html").exists()

    preview = (latest / "preview.md").read_text()
    assert "Instagram Pipeline Preview" in preview
    assert "Ranked Concepts" in preview
    assert "Adapter Version" in preview
