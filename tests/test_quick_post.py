from datetime import datetime
from auto.cli import publish as tasks
from auto.db import SessionLocal  # noqa: E402
from auto.models import Post, PostStatus  # noqa: E402


def test_quick_post_schedules(monkeypatch, test_db_engine):
    with SessionLocal() as session:
        session.add(
            Post(
                id="1",
                title="One",
                link="http://1",
                summary="",
                published="2000",
                created_at=datetime(2000, 1, 1),
            )
        )
        session.add(
            Post(
                id="2",
                title="Two",
                link="http://2",
                summary="",
                published="1999",
                created_at=datetime(1999, 1, 1),
            )
        )
        session.add(PostStatus(post_id="1", network="mastodon", status="published"))
        session.commit()

    monkeypatch.setattr("builtins.input", lambda prompt="": "y")

    tasks.quick_post()

    with SessionLocal() as session:
        ps = session.get(PostStatus, {"post_id": "2", "network": "mastodon"})
        assert ps is not None
        assert ps.status == "pending"


def test_quick_post_abort(monkeypatch, test_db_engine):
    with SessionLocal() as session:
        session.add(
            Post(
                id="1",
                title="One",
                link="http://1",
                summary="",
                published="2000",
                created_at=datetime(2000, 1, 1),
            )
        )
        session.commit()

    monkeypatch.setattr("builtins.input", lambda prompt="": "n")

    tasks.quick_post()

    with SessionLocal() as session:
        statuses = session.query(PostStatus).all()
        assert statuses == []
