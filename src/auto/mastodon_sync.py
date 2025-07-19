import asyncio
import logging

from sqlalchemy.orm import Session

from .socials.mastodon_client import MastodonClient
from .scheduler import register_task_handler
from .models import Post, PostStatus, Task
from .config import get_mastodon_sync_debug

logger = logging.getLogger(__name__)


async def _fetch_status_texts(client: MastodonClient) -> list[str]:
    statuses = await client.fetch_all_statuses()
    return [s.get("content", "") for s in statuses]


@register_task_handler("sync_mastodon_posts")
async def handle_sync_mastodon_posts(task: Task, session: Session) -> None:
    """Mark posts as published if they already appear on Mastodon."""
    client = MastodonClient()
    texts = await _fetch_status_texts(client)

    print(f"Fetched {len(texts)} Mastodon statuses")
    if get_mastodon_sync_debug():
        for text in texts:
            snippet = text.replace("\n", " ")
            print(f"STATUS: {snippet}")

    posts = session.query(Post).all()

    for post in posts:
        if any(post.link in t or post.id in t for t in texts):
            print(f"Post {post.id} already published")
            status = session.get(PostStatus, {"post_id": post.id, "network": "mastodon"})
            if status is None:
                status = PostStatus(post_id=post.id, network="mastodon", status="published")
                session.add(status)
            else:
                status.status = "published"
    session.commit()
