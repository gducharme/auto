"""Task handler for publishing posts after successful replays."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from .scheduler import register_task_handler
from .models import Task, PostStatus
from .config import get_replay_check_interval


@register_task_handler("publish_completed_replays")
async def handle_publish_completed_replays(task: Task, session: Session) -> None:
    """Mark posts as published when their replay_fixture task completed."""
    completed = (
        session.query(Task)
        .filter(
            Task.type == "replay_fixture",
            Task.status == "completed",
        )
        .all()
    )

    for replay_task in completed:
        data = json.loads(replay_task.payload or "{}")
        post_id = data.get("post_id")
        network = data.get("network")
        if not post_id or not network:
            continue
        status = session.get(PostStatus, {"post_id": post_id, "network": network})
        if status is None:
            status = PostStatus(post_id=post_id, network=network, status="published")
            session.add(status)
        else:
            status.status = "published"
    session.commit()

    next_run = datetime.now(timezone.utc) + timedelta(seconds=get_replay_check_interval())
    session.add(Task(type="publish_completed_replays", scheduled_at=next_run))
    session.commit()



def ensure_initial_task(session: Session) -> None:
    """Ensure at least one publish_completed_replays task exists."""
    exists = session.query(Task).filter(Task.type == "publish_completed_replays").first()
    if not exists:
        session.add(Task(type="publish_completed_replays"))

