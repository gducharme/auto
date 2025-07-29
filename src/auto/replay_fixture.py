"""Scheduler handler for replaying automation fixtures."""

from __future__ import annotations

import json
from sqlalchemy.orm import Session

from .scheduler import register_task_handler
from .models import Task
from .automation.replay import replay_fixture


@register_task_handler("replay_fixture")
async def handle_replay_fixture(task: Task, session: Session) -> None:
    """Replay recorded Safari commands."""
    data = json.loads(task.payload or "{}")
    name = data.get("name")
    post_id = data.get("post_id")
    network = data.get("network")
    if not name or not post_id or not network:
        raise ValueError("name, post_id and network are required")
    replay_fixture(name=name, post_id=post_id, network=network)
