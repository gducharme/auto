"""Handler for ingest_feed tasks."""

import logging
from datetime import datetime, timezone, timedelta

from .feeds.ingestion import run_ingest_async
from .config import get_ingest_interval
from .models import Task
from .scheduler import Scheduler

logger = logging.getLogger(__name__)


@Scheduler.register_task_handler("ingest_feed")
async def handle_ingest_feed(task: Task, session) -> None:
    """Run feed ingestion and schedule the next run."""
    try:
        await run_ingest_async()
    finally:
        next_run = datetime.now(timezone.utc) + timedelta(seconds=get_ingest_interval())
        session.add(Task(type="ingest_feed", scheduled_at=next_run))


def ensure_initial_task(session) -> None:
    """Ensure at least one ingest_feed task exists."""
    exists = session.query(Task).filter(Task.type == "ingest_feed").first()
    if not exists:
        session.add(Task(type="ingest_feed"))
