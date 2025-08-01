import asyncio
import anyio
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable, Dict
from sqlalchemy.orm import Session
import json

from jinja2 import Template

from sqlalchemy import and_, or_

from .models import PostStatus, Post, PostPreview, Task

from .db import SessionLocal, get_engine
from .socials.registry import get_registry

# Temporary alias for tests using the old PLUGINS mapping
from .metrics import POSTS_PUBLISHED, POSTS_FAILED
from .utils.periodic import PeriodicWorker
from .config import (
    get_poll_interval,
    get_post_delay,
    get_max_attempts,
)
from .preview import create_preview as _create_preview

logger = logging.getLogger(__name__)

TASK_HANDLERS: Dict[str, Callable[[Task, Session], Awaitable[None]]] = {}


def _load_default_handlers() -> None:
    """Import modules that register built-in task handlers."""
    # Imported for side effects of register_task_handler
    from . import ingest_scheduler, replay_fixture, replay_scanner  # noqa: F401


def register_task_handler(
    name: str,
) -> Callable[
    [Callable[[Task, Session], Awaitable[None]]],
    Callable[[Task, Session], Awaitable[None]],
]:
    def decorator(func: Callable[[Task, Session], Awaitable[None]]):
        TASK_HANDLERS[name] = func
        return func

    return decorator


async def _publish(status: PostStatus, session: Session) -> None:
    post = session.get(Post, status.post_id)
    if not post:
        logger.error("Post %s not found", status.post_id)
        status.status = "error"
        status.last_error = "post not found"
        status.attempts += 1
        session.commit()
        return
    try:
        plugin_registry = get_registry()
        plugin = plugin_registry.get(status.network)
        if plugin is None:
            raise ValueError(f"Unsupported network {status.network}")
        preview = session.get(
            PostPreview,
            {"post_id": status.post_id, "network": status.network},
        )
        if preview:
            text = Template(preview.content).render(post=post)
        else:
            text = f"{post.title} {post.link}"
        await plugin.post(text, visibility="unlisted")
        status.status = "published"
        status.last_error = None
        POSTS_PUBLISHED.labels(network=status.network).inc()
    except Exception as exc:
        status.status = "error"
        status.last_error = str(exc)
        logger.error("Failed to publish %s: %s", status.post_id, exc)
        POSTS_FAILED.labels(network=status.network).inc()
    finally:
        status.attempts += 1
        session.commit()
        await asyncio.sleep(get_post_delay())


@register_task_handler("publish_post")
async def handle_publish_post(task: Task, session: Session) -> None:
    data = json.loads(task.payload or "{}")
    post_id = data.get("post_id")
    network = data.get("network")
    status = session.get(PostStatus, {"post_id": post_id, "network": network})
    if status is None:
        raise ValueError(f"status not found for {post_id}/{network}")
    await _publish(status, session)


@register_task_handler("create_preview")
async def handle_create_preview(task: Task, session: Session) -> None:
    data = json.loads(task.payload or "{}")
    post_id = data.get("post_id")
    network = data.get("network", "mastodon")
    _create_preview(session, post_id, network)


async def process_pending(max_attempts: Optional[int] = None) -> None:
    """Fetch due tasks and dispatch them to registered handlers."""
    _load_default_handlers()
    now = datetime.now(timezone.utc)
    if max_attempts is None:
        max_attempts = get_max_attempts()
    with SessionLocal() as session:
        logger.debug("Searching for tasks due before %s", now.isoformat())
        tasks = (
            session.query(Task)
            .filter(
                Task.scheduled_at <= now,
                or_(
                    Task.status == "pending",
                    and_(Task.status == "error", Task.attempts < max_attempts),
                ),
            )
            .order_by(Task.scheduled_at)
            .all()
        )
        logger.debug("Found %d task(s)", len(tasks))

        for task in tasks:
            handler = TASK_HANDLERS.get(task.type)
            if handler is None:
                task.status = "error"
                task.last_error = f"no handler for {task.type}"
                task.attempts += 1
                session.commit()
                continue
            task.status = "running"
            session.commit()
            try:
                await handler(task, session)
                task.status = "completed"
                task.last_error = None
            except Exception as exc:
                task.status = "error"
                task.last_error = str(exc)
                logger.error("Task %s failed: %s", task.type, exc)
            finally:
                task.attempts += 1
                session.commit()


async def _scheduler_iteration() -> None:
    await process_pending()


async def run_scheduler() -> None:
    """Run the scheduler loop until cancelled."""
    from . import configure_logging

    configure_logging()
    sched = Scheduler()
    task = await sched.start()
    if task is None:
        return

    logger.info("Scheduler started; press Ctrl+C to exit")
    try:
        await task
    finally:
        await sched.stop()
        logger.info("Scheduler stopped")


class Scheduler:
    """Manage the background scheduler task without relying on globals."""

    def __init__(self) -> None:
        self._worker = PeriodicWorker(_scheduler_iteration, get_poll_interval)

    async def start(self) -> Optional[asyncio.Task]:
        """Start the background scheduler loop."""
        if self._worker.task is None or self._worker.task.done():
            from sqlalchemy import inspect

            inspector = inspect(get_engine())
            if not inspector.has_table("tasks"):
                logger.warning("tasks table missing; scheduler not started")
                return None

            # ensure ingest handler and other task handlers are registered
            from . import ingest_scheduler, replay_fixture, replay_scanner  # noqa: F401

            with SessionLocal() as session:
                ingest_scheduler.ensure_initial_task(session)
                replay_scanner.ensure_initial_task(session)
                session.commit()

            await self._worker.start()
        return self._worker.task

    async def stop(self) -> None:
        """Stop the background scheduler loop."""
        await self._worker.stop()


def main():
    anyio.run(run_scheduler)


if __name__ == "__main__":
    main()
