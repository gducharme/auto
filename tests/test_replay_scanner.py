import asyncio
import json
from datetime import datetime, timedelta, timezone

from auto.db import SessionLocal
from auto.models import Task, PostStatus
from auto.replay_scanner import handle_publish_completed_replays


async def run(task, session):
    await handle_publish_completed_replays(task, session)


def test_publish_completed_replays_task(test_db_engine, monkeypatch):
    monkeypatch.setenv("REPLAY_CHECK_INTERVAL", "0")
    with SessionLocal() as session:
        # completed replay task
        session.add(
            Task(
                type="replay_fixture",
                status="completed",
                payload=json.dumps({"post_id": "1", "network": "mastodon"}),
            )
        )
        # task to trigger scanner
        task = Task(
            type="publish_completed_replays",
            scheduled_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        session.add(task)
        session.commit()
        task_id = task.id

    with SessionLocal() as session:
        db_task = session.get(Task, task_id)
        assert db_task is not None
        asyncio.run(run(db_task, session))

        status = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert status is not None
        assert status.status == "published"
        # new task scheduled
        next_task = (
            session.query(Task)
            .filter(Task.type == "publish_completed_replays")
            .order_by(Task.id.desc())
            .first()
        )
        assert next_task is not None
        assert next_task.id != task_id


