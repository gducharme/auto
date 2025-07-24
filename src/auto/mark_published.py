"""Task handler for marking a post as published."""

from __future__ import annotations

import json
import logging
from sqlalchemy.orm import Session

from .scheduler import register_task_handler
from .models import PostStatus, Task

logger = logging.getLogger(__name__)


@register_task_handler("mark_published")
async def handle_mark_published(task: Task, session: Session) -> None:
    """Mark ``post_id`` as published on ``network``."""
    data = json.loads(task.payload or "{}")
    post_id = data.get("post_id")
    network = data.get("network")
    if not post_id or not network:
        raise ValueError("post_id and network are required")

    status = session.get(PostStatus, {"post_id": post_id, "network": network})
    if status is None:
        status = PostStatus(post_id=post_id, network=network, status="published")
        session.add(status)
    else:
        status.status = "published"
    session.commit()
