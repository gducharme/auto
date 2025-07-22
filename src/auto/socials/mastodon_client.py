import asyncio
import anyio
import logging
from typing import Dict, List
import httpx

from .base import SocialPlugin
from ..config import get_mastodon_instance, get_mastodon_token

logger = logging.getLogger(__name__)


def fetch_trending_tags(limit: int = 10) -> List[str]:
    """Return a list of trending tag names from Mastodon."""
    from mastodon import Mastodon

    instance = get_mastodon_instance()
    token = get_mastodon_token()

    try:
        masto = Mastodon(access_token=token, api_base_url=instance)
        tags = masto.trending_tags(limit=limit)
        names = [
            tag["name"] if isinstance(tag, dict) else getattr(tag, "name", str(tag))
            for tag in tags
        ]
        return names
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Failed to fetch trending tags: %s", exc)
        return []


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

    async def fetch_all_statuses(self) -> list[dict]:
        """Return all statuses for the authenticated account."""
        from mastodon import Mastodon

        token = get_mastodon_token()
        instance = get_mastodon_instance()

        def _sync_fetch() -> list[dict]:
            masto = Mastodon(access_token=token, api_base_url=instance)
            me = masto.account_verify_credentials()
            account_id = me["id"]
            statuses: list[dict] = []
            max_id = None
            while True:
                page = masto.account_statuses(account_id, max_id=max_id, limit=40)
                if not page:
                    break
                statuses.extend(page)
                max_id = page[-1]["id"]
            return statuses

        return await asyncio.to_thread(_sync_fetch)


async def post_to_mastodon_async(status: str, visibility: str = "private") -> None:
    """Backward-compatible wrapper around :class:`MastodonClient`."""
    client = MastodonClient()
    await client.post(status, visibility=visibility)


def post_to_mastodon(status: str, visibility: str = "private") -> None:
    """Synchronous wrapper for :func:`post_to_mastodon_async`."""
    anyio.run(post_to_mastodon_async, status, visibility)


if __name__ == "__main__":
    anyio.run(
        post_to_mastodon_async, "Hello world! My Substack → Socials bot is live 🚀"
    )
