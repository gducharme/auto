from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta

import pytest

from auto.cli import publish
from auto.db import SessionLocal
from auto.models import Post, PostPreview, PostStatus, Task
from auto.scheduler import process_pending
from auto.socials.registry import get_registry, reset_registry


class FakeMastodonPlugin:
    network = "mastodon"

    def __init__(self) -> None:
        self.posts: list[tuple[str, str]] = []

    async def post(self, text: str, visibility: str = "unlisted") -> None:
        self.posts.append((text, visibility))

    async def fetch_metrics(self, post_id: str) -> dict[str, int]:
        return {}


@pytest.mark.integration
def test_auto_publish_pipeline_uses_scheduled_task_and_preview(
    test_db_engine, monkeypatch
):
    """Schedule a post and verify scheduler publishes with rendered preview text."""
    reset_registry()
    plugin = FakeMastodonPlugin()
    get_registry().register(plugin)
    monkeypatch.setenv("POST_DELAY", "0")

    with SessionLocal() as session:
        session.add(
            Post(
                id="post-1",
                title="Pipeline Check",
                link="https://example.com/pipeline-check",
                summary="",
                published="",
            )
        )
        session.commit()

    publish.schedule(post_id="post-1", time="in 0s", network="mastodon")

    with SessionLocal() as session:
        session.add(
            PostPreview(
                post_id="post-1",
                network="mastodon",
                content="Draft: {{ post.title }} {{ post.link }}",
            )
        )
        session.commit()

    asyncio.run(process_pending())

    with SessionLocal() as session:
        status = session.get(PostStatus, {"post_id": "post-1", "network": "mastodon"})
        assert status is not None
        assert status.status == "published"

        task = (
            session.query(Task)
            .filter(Task.type == "publish_post")
            .order_by(Task.id.desc())
            .first()
        )
        assert task is not None
        assert task.status == "completed"
        scheduled_at = task.scheduled_at
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
        assert scheduled_at <= datetime.now(timezone.utc) + timedelta(seconds=1)

    assert plugin.posts == [
        ("Draft: Pipeline Check https://example.com/pipeline-check", "unlisted")
    ]


@pytest.mark.integration
def test_auto_publish_pipeline_falls_back_to_title_and_link(
    test_db_engine, monkeypatch
):
    """Without preview content, scheduler should publish ``<title> <link>``."""
    reset_registry()
    plugin = FakeMastodonPlugin()
    get_registry().register(plugin)
    monkeypatch.setenv("POST_DELAY", "0")

    with SessionLocal() as session:
        session.add(
            Post(
                id="post-2",
                title="Fallback Title",
                link="https://example.com/fallback",
                summary="",
                published="",
            )
        )
        session.commit()

    publish.schedule(post_id="post-2", time="in 0s", network="mastodon")
    asyncio.run(process_pending())

    with SessionLocal() as session:
        status = session.get(PostStatus, {"post_id": "post-2", "network": "mastodon"})
        assert status is not None
        assert status.status == "published"

    assert plugin.posts == [("Fallback Title https://example.com/fallback", "unlisted")]
