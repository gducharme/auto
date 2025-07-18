import asyncio
import logging
import httpx

from ..config import get_mastodon_instance, get_mastodon_token

logger = logging.getLogger(__name__)


async def post_to_mastodon_async(status: str, visibility: str = "private") -> None:
    """Post a status to Mastodon asynchronously."""
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


def post_to_mastodon(status: str, visibility: str = "private") -> None:
    """Synchronous wrapper for :func:`post_to_mastodon_async`."""
    asyncio.run(post_to_mastodon_async(status=status, visibility=visibility))


if __name__ == "__main__":
    post_to_mastodon("Hello world! My Substack → Socials bot is live 🚀")
