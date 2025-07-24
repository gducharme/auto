import asyncio
import json

from auto.db import SessionLocal
from auto.models import PostStatus, Task
from auto.mark_published import handle_mark_published


async def run(task, session):
    await handle_mark_published(task, session)


def test_mark_published_creates_status(test_db_engine):
    with SessionLocal() as session:
        task = Task(
            type="mark_published",
            payload=json.dumps({"post_id": "1", "network": "mastodon"}),
        )
        session.add(task)
        session.commit()

        asyncio.run(run(task, session))

        status = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert status is not None
        assert status.status == "published"


def test_mark_published_updates_existing(test_db_engine):
    with SessionLocal() as session:
        session.add(
            PostStatus(post_id="1", network="mastodon", status="pending")
        )
        task = Task(
            type="mark_published",
            payload=json.dumps({"post_id": "1", "network": "mastodon"}),
        )
        session.add(task)
        session.commit()

        asyncio.run(run(task, session))

        status = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert status.status == "published"
