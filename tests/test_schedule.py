from invoke import Context

import tasks  # noqa: E402
from auto.db import SessionLocal  # noqa: E402
from auto.models import PostStatus


def test_schedule_missing_post(monkeypatch, test_db_engine, capsys):
    tasks.schedule(Context(), post_id="missing", time="in 1s")

    captured = capsys.readouterr()
    assert "Post missing not found" in captured.out

    with SessionLocal() as session:
        statuses = session.query(PostStatus).all()
        assert statuses == []


def test_schedule_naive_timestamp(test_db_engine):
    from datetime import datetime, timezone
    from auto.models import Post

    ts = "2023-01-02T12:34:56"
    with SessionLocal() as session:
        session.add(
            Post(
                id="1",
                title="Title",
                link="http://example",
                summary="",
                published="",
            )
        )
        session.commit()

    tasks.schedule(Context(), post_id="1", time=ts)

    with SessionLocal() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps is not None
        assert ps.scheduled_at == datetime(2023, 1, 2, 12, 34, 56, tzinfo=timezone.utc)
        assert ps.scheduled_at.tzinfo is timezone.utc

