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

