import asyncio
from datetime import datetime, timedelta, timezone
import json

from auto.db import SessionLocal
from auto.models import Post, PostStatus, Task, PostPreview
from auto.socials.registry import get_registry, reset_registry
from auto.socials.mastodon_client import MastodonClient
import pytest
from auto.scheduler import process_pending, Scheduler
from auto.metrics import POSTS_PUBLISHED, POSTS_FAILED


class DummyPoster:
    called = False

    @classmethod
    def post(cls, text):
        cls.called = True


@pytest.fixture(autouse=True)
def setup_plugins():
    reset_registry()
    reg = get_registry()
    reg.register(MastodonClient())
    yield
    reset_registry()


async def run_process():
    await process_pending()


def test_publish_post_task(test_db_engine, monkeypatch):
    DummyPoster.called = False

    with SessionLocal() as session:
        post = Post(
            id="1", title="Title", link="http://example", summary="", published=""
        )
        session.add(post)
        status = PostStatus(
            post_id="1",
            network="mastodon",
            scheduled_at=datetime.now(timezone.utc),
        )
        session.add(status)
        task = Task(
            type="publish_post",
            payload=json.dumps({"post_id": "1", "network": "mastodon"}),
            scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        session.add(task)
        session.commit()
        task_id = task.id

    async def fake_post(text, visibility="unlisted"):
        DummyPoster.post(text)

    plugin = get_registry().get("mastodon")
    assert plugin is not None
    monkeypatch.setattr(plugin, "post", fake_post)
    monkeypatch.setenv("POST_DELAY", "0")

    start = POSTS_PUBLISHED.labels(network="mastodon")._value.get()
    fail_start = POSTS_FAILED.labels(network="mastodon")._value.get()

    asyncio.run(run_process())

    with SessionLocal() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps.status == "published"
        t = session.get(Task, task_id)
        assert t.status == "completed"
    assert DummyPoster.called
    assert POSTS_PUBLISHED.labels(network="mastodon")._value.get() == start + 1
    assert POSTS_FAILED.labels(network="mastodon")._value.get() == fail_start


def test_import_before_plugin_setup(test_db_engine, monkeypatch):
    """Importing scheduler before registering plugins should not break."""
    reset_registry()
    DummyPoster.called = False

    with SessionLocal() as session:
        post = Post(
            id="4", title="T4", link="http://example4", summary="", published=""
        )
        session.add(post)
        status = PostStatus(
            post_id="4", network="mastodon", scheduled_at=datetime.now(timezone.utc)
        )
        session.add(status)
        task = Task(
            type="publish_post",
            payload=json.dumps({"post_id": "4", "network": "mastodon"}),
            scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        session.add(task)
        session.commit()
        task_id = task.id

    reg = get_registry()
    reg.register(MastodonClient())

    async def fake_post(text, visibility="unlisted"):
        DummyPoster.post(text)

    plugin = reg.get("mastodon")
    assert plugin is not None
    monkeypatch.setattr(plugin, "post", fake_post)
    monkeypatch.setenv("POST_DELAY", "0")

    start = POSTS_PUBLISHED.labels(network="mastodon")._value.get()

    asyncio.run(run_process())

    with SessionLocal() as session:
        ps = session.get(PostStatus, {"post_id": "4", "network": "mastodon"})
        assert ps.status == "published"
        t = session.get(Task, task_id)
        assert t.status == "completed"
    assert DummyPoster.called
    assert POSTS_PUBLISHED.labels(network="mastodon")._value.get() == start + 1


def test_ingest_feed_task(test_db_engine, monkeypatch):
    called = {"count": 0}

    async def fake_run_ingest_async():
        called["count"] += 1

    monkeypatch.setattr("auto.feeds.ingestion.run_ingest_async", fake_run_ingest_async)
    monkeypatch.setattr("auto.ingest_scheduler.run_ingest_async", fake_run_ingest_async)
    monkeypatch.setenv("INGEST_INTERVAL", "0")

    with SessionLocal() as session:
        task = Task(
            type="ingest_feed",
            scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        session.add(task)
        session.commit()

    asyncio.run(run_process())

    assert called["count"] == 1

    with SessionLocal() as session:
        next_task = (
            session.query(Task)
            .filter(Task.type == "ingest_feed")
            .order_by(Task.id.desc())
            .first()
        )
        assert next_task is not None


def test_publish_failure_metrics(test_db_engine, monkeypatch):
    with SessionLocal() as session:
        post = Post(
            id="2", title="Title", link="http://example", summary="", published=""
        )
        session.add(post)
        status = PostStatus(
            post_id="2",
            network="mastodon",
            scheduled_at=datetime.now(timezone.utc),
        )
        session.add(status)
        task = Task(
            type="publish_post",
            payload=json.dumps({"post_id": "2", "network": "mastodon"}),
            scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        session.add(task)
        session.commit()
        task_id = task.id

    async def fail_post(text, visibility="unlisted"):
        raise RuntimeError("boom")

    plugin = get_registry().get("mastodon")
    assert plugin is not None
    monkeypatch.setattr(plugin, "post", fail_post)
    monkeypatch.setenv("POST_DELAY", "0")

    start = POSTS_FAILED.labels(network="mastodon")._value.get()

    asyncio.run(run_process())

    with SessionLocal() as session:
        ps = session.get(PostStatus, {"post_id": "2", "network": "mastodon"})
        assert ps.status == "error"
        t = session.get(Task, task_id)
        assert t.status == "completed"
    assert POSTS_FAILED.labels(network="mastodon")._value.get() == start + 1


def test_create_preview_task(test_db_engine):
    with SessionLocal() as session:
        post = Post(
            id="3", title="T3", link="http://example3", summary="", published=""
        )
        session.add(post)
        session.add(
            PostStatus(
                post_id="3",
                network="mastodon",
                scheduled_at=datetime.now(timezone.utc),
            )
        )
        task = Task(
            type="create_preview",
            payload=json.dumps({"post_id": "3", "network": "mastodon"}),
            scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        session.add(task)
        session.commit()
        task_id = task.id

    asyncio.run(run_process())

    with SessionLocal() as session:
        preview = session.get(PostPreview, {"post_id": "3", "network": "mastodon"})
        assert preview is not None
        t = session.get(Task, task_id)
        assert t.status == "completed"


def test_scheduler_start_stop(test_db_engine, monkeypatch):
    monkeypatch.setattr("auto.ingest_scheduler.ensure_initial_task", lambda s: None)
    monkeypatch.setenv("SCHEDULER_POLL_INTERVAL", "0")

    sched = Scheduler()

    async def run():
        task = await sched.start()
        assert task is sched._worker.task
        await asyncio.sleep(0.01)
        await sched.stop()
        assert sched._worker.task is None

    asyncio.run(run())
