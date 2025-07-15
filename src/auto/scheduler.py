import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from .db import SessionLocal, engine
from .models import PostStatus, Post
from .socials.mastodon_client import post_to_mastodon

logger = logging.getLogger(__name__)

POLL_INTERVAL = int(os.getenv("SCHEDULER_POLL_INTERVAL", "5"))
POST_DELAY = float(os.getenv("POST_DELAY", "1"))

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
            await asyncio.to_thread(post_to_mastodon, f"{post.title} {post.link}")
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
        await asyncio.sleep(POST_DELAY)

async def process_pending():
    now = datetime.utcnow()
    with SessionLocal() as session:
        statuses = (
            session.query(PostStatus)
            .filter(PostStatus.status == "pending", PostStatus.scheduled_at <= now)
            .order_by(PostStatus.scheduled_at)
            .all()
        )
        for status in statuses:
            await _publish(status, session)

async def run_scheduler():
    while True:
        await process_pending()
        await asyncio.sleep(POLL_INTERVAL)


_task = None


async def start() -> Optional[asyncio.Task]:
    """Start the background scheduler loop."""
    global _task
    if _task is None or _task.done():
        from sqlalchemy import inspect

        inspector = inspect(engine)
        if not inspector.has_table("post_status"):
            logger.warning("post_status table missing; scheduler not started")
            return None
        _task = asyncio.create_task(run_scheduler())
    return _task


async def stop() -> None:
    """Stop the background scheduler loop."""
    global _task
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None


def main():
    asyncio.run(run_scheduler())

if __name__ == "__main__":
    main()
