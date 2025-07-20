from datetime import datetime, timezone

from auto.cli import publish as tasks
from auto.db import SessionLocal
from auto.models import Post, PostStatus


def _setup_posts() -> None:
    with SessionLocal() as session:
        session.add(
            Post(
                id="1",
                title="One",
                link="http://1",
                summary="",
                published="2020",
                created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
            )
        )
        session.add(
            Post(
                id="2",
                title="Two",
                link="http://2",
                summary="",
                published="2019",
                created_at=datetime(2019, 1, 1, tzinfo=timezone.utc),
            )
        )
        session.add(PostStatus(post_id="1", network="mastodon", status="published"))
        session.commit()


def test_list_substacks_outputs(test_db_engine, capsys):
    _setup_posts()

    tasks.list_substacks()

    out = capsys.readouterr().out
    assert "1\tOne\tpublished" in out
    assert "2\tTwo\tpending" in out


def test_list_substacks_filters(test_db_engine, capsys):
    _setup_posts()

    tasks.list_substacks(published=True, unpublished=False)
    out = capsys.readouterr().out
    assert "One" in out
    assert "Two" not in out

    tasks.list_substacks(published=False, unpublished=True)
    out = capsys.readouterr().out
    assert "One" not in out
    assert "Two" in out
