import asyncio
from datetime import datetime, timedelta, timezone

from auto.db import SessionLocal
from auto.models import Post, PostStatus, PostPreview
from auto.scheduler import process_pending


class DummyPoster:
    called = False

    @classmethod
    def post(cls, text):
        cls.called = True


def test_process_pending_publishes(test_db_engine, monkeypatch):
    DummyPoster.called = False
    session_factory = SessionLocal

    with session_factory() as session:
        post = Post(
            id="1", title="Title", link="http://example", summary="", published=""
        )
        session.add(post)
        status = PostStatus(
            post_id="1",
            network="mastodon",
            scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        session.add(status)
        session.commit()

    async def fake_post(text, visibility="unlisted"):
        DummyPoster.post(text)

    monkeypatch.setattr(
        "auto.scheduler.post_to_mastodon_async",
        fake_post,
    )

    monkeypatch.setenv("POST_DELAY", "0")

    asyncio.run(process_pending())

    with session_factory() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps.status == "published"
    assert DummyPoster.called


def test_process_pending_retries_error(test_db_engine, monkeypatch):
    DummyPoster.called = False
    session_factory = SessionLocal

    with session_factory() as session:
        post = Post(
            id="1", title="Title", link="http://example", summary="", published=""
        )
        session.add(post)
        status = PostStatus(
            post_id="1",
            network="mastodon",
            status="error",
            attempts=1,
            scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        session.add(status)
        session.commit()

    async def fake_post(text, visibility="unlisted"):
        DummyPoster.post(text)

    monkeypatch.setattr(
        "auto.scheduler.post_to_mastodon_async",
        fake_post,
    )

    monkeypatch.setenv("POST_DELAY", "0")

    asyncio.run(process_pending())

    with session_factory() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps.status == "published"
        assert ps.attempts == 2
    assert DummyPoster.called


def test_process_pending_ignores_exceeded_attempts(test_db_engine, monkeypatch):
    DummyPoster.called = False
    session_factory = SessionLocal

    with session_factory() as session:
        post = Post(
            id="1", title="Title", link="http://example", summary="", published=""
        )
        session.add(post)
        status = PostStatus(
            post_id="1",
            network="mastodon",
            status="error",
            attempts=3,
            scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        session.add(status)
        session.commit()

    async def fake_post(text, visibility="unlisted"):
        DummyPoster.post(text)

    monkeypatch.setattr(
        "auto.scheduler.post_to_mastodon_async",
        fake_post,
    )

    monkeypatch.setenv("POST_DELAY", "0")

    asyncio.run(process_pending())

    with session_factory() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps.status == "error"
        assert ps.attempts == 3
    assert not DummyPoster.called


def test_process_pending_uses_preview(test_db_engine, monkeypatch):
    DummyPoster.called = False
    captured = {}
    session_factory = SessionLocal

    with session_factory() as session:
        post = Post(
            id="1", title="Title", link="http://example", summary="", published=""
        )
        session.add(post)
        status = PostStatus(
            post_id="1",
            network="mastodon",
            scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        preview = PostPreview(
            post_id="1", network="mastodon", content="Look {{ post.title }} {{ post.link }}"
        )
        session.add_all([status, preview])
        session.commit()

    async def fake_post(text, visibility="unlisted"):
        captured["text"] = text
        DummyPoster.post(text)

    monkeypatch.setattr("auto.scheduler.post_to_mastodon_async", fake_post)

    monkeypatch.setenv("POST_DELAY", "0")

    asyncio.run(process_pending())

    with session_factory() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps.status == "published"
    assert captured.get("text") == "Look Title http://example"
