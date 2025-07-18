import asyncio
import logging
from typing import Dict
import httpx

from .base import SocialPlugin
from ..config import get_mastodon_instance, get_mastodon_token

logger = logging.getLogger(__name__)


class MastodonClient(SocialPlugin):
    """SocialPlugin implementation for Mastodon."""

    network = "mastodon"

    async def post(self, status: str, visibility: str = "private") -> None:
        token = get_mastodon_token()
        instance = get_mastodon_instance()
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{instance}/api/v1/statuses",
                    data={"status": status, "visibility": visibility},
                    headers=headers,
                )
                resp.raise_for_status()
            logger.info("Posted to Mastodon")
        except Exception as exc:
            logger.error("Failed to post to Mastodon: %s", exc)
            raise

    async def fetch_metrics(self, post_id: str) -> Dict[str, int]:
        token = get_mastodon_token()
        instance = get_mastodon_instance()
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{instance}/api/v1/statuses/{post_id}", headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "replies": data.get("replies_count", 0),
                "reblogs": data.get("reblogs_count", 0),
                "favourites": data.get("favourites_count", 0),
            }


async def post_to_mastodon_async(status: str, visibility: str = "private") -> None:
    """Backward-compatible wrapper around :class:`MastodonClient`."""
    client = MastodonClient()
    await client.post(status, visibility=visibility)


def post_to_mastodon(status: str, visibility: str = "private") -> None:
    """Synchronous wrapper for :func:`post_to_mastodon_async`."""
    asyncio.run(post_to_mastodon_async(status=status, visibility=visibility))


if __name__ == "__main__":
    asyncio.run(
        post_to_mastodon_async("Hello world! My Substack → Socials bot is live 🚀")
    )
