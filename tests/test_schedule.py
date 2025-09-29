from auto.cli import publish as tasks
from auto.cli.helpers import _parse_when  # noqa: E402
from auto.db import SessionLocal  # noqa: E402
from auto.models import PostStatus


def test_schedule_missing_post(monkeypatch, test_db_engine, capsys):
    tasks.schedule(post_id="missing", time="in 1s")

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

    tasks.schedule(post_id="1", time=ts)

    with SessionLocal() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps is not None
        assert ps.scheduled_at == datetime(2023, 1, 2, 12, 34, 56, tzinfo=timezone.utc)
        assert ps.scheduled_at.tzinfo is timezone.utc


def test_schedule_aware_timestamp(test_db_engine):
    from datetime import datetime, timezone
    from auto.models import Post

    ts = "2023-01-02T12:34:56-05:00"
    with SessionLocal() as session:
        session.add(
            Post(
                id="2",
                title="Title",
                link="http://example",
                summary="",
                published="",
            )
        )
        session.commit()

    tasks.schedule(post_id="2", time=ts)

    with SessionLocal() as session:
        ps = session.get(PostStatus, {"post_id": "2", "network": "mastodon"})
        assert ps is not None
        assert ps.scheduled_at == datetime(2023, 1, 2, 17, 34, 56, tzinfo=timezone.utc)
        assert ps.scheduled_at.tzinfo is timezone.utc


def test_parse_when_naive():
    from datetime import datetime, timezone

    result = _parse_when("2023-01-02T01:02:03")
    assert result == datetime(2023, 1, 2, 1, 2, 3, tzinfo=timezone.utc)
    assert result.tzinfo is timezone.utc


def test_parse_when_aware():
    from datetime import datetime, timezone

    result = _parse_when("2023-01-02T01:02:03+02:00")
    assert result == datetime(2023, 1, 1, 23, 2, 3, tzinfo=timezone.utc)
    assert result.tzinfo is timezone.utc


def test_list_schedule_outputs(test_db_engine, capsys):
    from datetime import datetime, timezone
    from auto.models import Post

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
        session.add(
            PostStatus(
                post_id="1",
                network="mastodon",
                scheduled_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
            )
        )
        session.commit()

    tasks.list_schedule()

    captured = capsys.readouterr()
    assert "1\tmastodon" in captured.out


def test_schedule_creates_task(test_db_engine):
    from datetime import datetime, timezone
    from auto.models import Post, Task
    import json

    ts = "2023-02-03T04:05:06Z"

    with SessionLocal() as session:
        session.add(
            Post(
                id="99", title="Title", link="http://example", summary="", published=""
            )
        )
        session.commit()

    tasks.schedule(post_id="99", time=ts, network="mastodon")

    with SessionLocal() as session:
        task = session.query(Task).filter(Task.type == "publish_post").one()
        assert json.loads(task.payload) == {"post_id": "99", "network": "mastodon"}
        expected = datetime(2023, 2, 3, 4, 5, 6, tzinfo=timezone.utc)
        assert task.scheduled_at.replace(tzinfo=timezone.utc) == expected
