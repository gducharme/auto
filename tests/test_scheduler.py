import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import create_engine
from auto.feeds.ingestion import init_db
from auto.db import SessionLocal
from auto.models import Post, PostStatus, PostPreview
from auto.scheduler import process_pending


class DummyPoster:
    called = False

    @classmethod
    def post(cls, text):
        cls.called = True


def test_process_pending_publishes(tmp_path, monkeypatch):
    DummyPoster.called = False
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    init_db(str(db_path), engine=engine)

    session_factory = SessionLocal
    # override engine used by SessionLocal
    monkeypatch.setattr("auto.db.get_engine", lambda: engine)

    with session_factory() as session:
        post = Post(
            id="1", title="Title", link="http://example", summary="", published=""
        )
        session.add(post)
        status = PostStatus(
            post_id="1",
            network="mastodon",
            scheduled_at=datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(seconds=1),
        )
        session.add(status)
        session.commit()

    monkeypatch.setattr(
        "auto.scheduler.post_to_mastodon",
        lambda text, visibility="unlisted": DummyPoster.post(text),
    )

    asyncio.run(process_pending())

    with session_factory() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps.status == "published"
    assert DummyPoster.called


def test_process_pending_retries_error(tmp_path, monkeypatch):
    DummyPoster.called = False
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    init_db(str(db_path), engine=engine)

    session_factory = SessionLocal
    monkeypatch.setattr("auto.db.get_engine", lambda: engine)

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
            scheduled_at=datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(seconds=1),
        )
        session.add(status)
        session.commit()

    monkeypatch.setattr(
        "auto.scheduler.post_to_mastodon",
        lambda text, visibility="unlisted": DummyPoster.post(text),
    )

    asyncio.run(process_pending())

    with session_factory() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps.status == "published"
        assert ps.attempts == 2
    assert DummyPoster.called


def test_process_pending_ignores_exceeded_attempts(tmp_path, monkeypatch):
    DummyPoster.called = False
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    init_db(str(db_path), engine=engine)

    session_factory = SessionLocal
    monkeypatch.setattr("auto.db.get_engine", lambda: engine)

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
            scheduled_at=datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(seconds=1),
        )
        session.add(status)
        session.commit()

    monkeypatch.setattr(
        "auto.scheduler.post_to_mastodon",
        lambda text, visibility="unlisted": DummyPoster.post(text),
    )

    asyncio.run(process_pending())

    with session_factory() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps.status == "error"
        assert ps.attempts == 3
    assert not DummyPoster.called


def test_process_pending_uses_preview(tmp_path, monkeypatch):
    DummyPoster.called = False
    captured = {}
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    init_db(str(db_path), engine=engine)

    session_factory = SessionLocal
    monkeypatch.setattr("auto.db.get_engine", lambda: engine)

    with session_factory() as session:
        post = Post(
            id="1", title="Title", link="http://example", summary="", published=""
        )
        session.add(post)
        status = PostStatus(
            post_id="1",
            network="mastodon",
            scheduled_at=datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(seconds=1),
        )
        preview = PostPreview(
            post_id="1", network="mastodon", content="Look {{ post.title }} {{ post.link }}"
        )
        session.add_all([status, preview])
        session.commit()

    def fake_post(text, visibility="unlisted"):
        captured["text"] = text
        DummyPoster.post(text)

    monkeypatch.setattr("auto.scheduler.post_to_mastodon", fake_post)

    asyncio.run(process_pending())

    with session_factory() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps.status == "published"
    assert captured.get("text") == "Look Title http://example"
