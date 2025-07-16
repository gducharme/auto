import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, or_

from .db import SessionLocal, get_engine
from .models import PostStatus, Post
from .socials.mastodon_client import post_to_mastodon

logger = logging.getLogger(__name__)


def get_poll_interval() -> int:
    """Return the scheduler poll interval in seconds."""
    return int(os.getenv("SCHEDULER_POLL_INTERVAL", "5"))


def get_post_delay() -> float:
    """Return the delay between publish attempts."""
    return float(os.getenv("POST_DELAY", "1"))


def get_max_attempts() -> int:
    """Return the maximum publish attempts."""
    return int(os.getenv("MAX_ATTEMPTS", "3"))


async def _publish(status: PostStatus, session):
    post = session.get(Post, status.post_id)
    if not post:
        logger.error("Post %s not found", status.post_id)
        status.status = "error"
        status.last_error = "post not found"
        status.attempts += 1
        session.commit()
        return
    try:
        if status.network == "mastodon":
            await asyncio.to_thread(
                post_to_mastodon,
                f"{post.title} {post.link}",
                visibility="unlisted",
            )
        else:
            raise ValueError(f"Unsupported network {status.network}")
        status.status = "published"
        status.last_error = None
    except Exception as exc:
        status.status = "error"
        status.last_error = str(exc)
        logger.error("Failed to publish %s: %s", status.post_id, exc)
    finally:
        status.attempts += 1
        session.commit()
        await asyncio.sleep(get_post_delay())


async def process_pending(max_attempts: Optional[int] = None):
    # use timezone-aware UTC datetime then drop tz info for DB comparison
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if max_attempts is None:
        max_attempts = get_max_attempts()
    with SessionLocal() as session:
        statuses = (
            session.query(PostStatus)
            .filter(
                PostStatus.scheduled_at <= now,
                or_(
                    PostStatus.status == "pending",
                    and_(
                        PostStatus.status == "error",
                        PostStatus.attempts < max_attempts,
                    ),
                ),
            )
            .order_by(PostStatus.scheduled_at)
            .all()
        )
        for status in statuses:
            await _publish(status, session)


async def run_scheduler():
    while True:
        await process_pending()
        await asyncio.sleep(get_poll_interval())


class Scheduler:
    """Manage the background scheduler task without using module-level globals."""

    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> Optional[asyncio.Task]:
        """Start the background scheduler loop."""
        if self._task is None or self._task.done():
            from sqlalchemy import inspect

            inspector = inspect(get_engine())
            if not inspector.has_table("post_status"):
                logger.warning("post_status table missing; scheduler not started")
                return None
            self._task = asyncio.create_task(run_scheduler())
        return self._task

    async def stop(self) -> None:
        """Stop the background scheduler loop."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


# provide a default scheduler instance for backwards compatibility
default_scheduler = Scheduler()


async def start() -> Optional[asyncio.Task]:
    """Start the default background scheduler loop."""
    return await default_scheduler.start()


async def stop() -> None:
    """Stop the default background scheduler loop."""
    await default_scheduler.stop()


def main():
    asyncio.run(run_scheduler())


if __name__ == "__main__":
    main()
