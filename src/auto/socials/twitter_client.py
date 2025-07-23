import logging
from typing import Dict

from .base import SocialPlugin

logger = logging.getLogger(__name__)


class TwitterClient(SocialPlugin):
    """Minimal Twitter plugin placeholder."""

    network = "twitter"

    async def post(self, text: str, visibility: str = "public") -> None:
        """Pretend to publish ``text`` to Twitter."""
        logger.info("Posting to Twitter: %s", text)

    async def fetch_metrics(self, post_id: str) -> Dict[str, int]:
        """Return dummy engagement metrics for ``post_id``."""
        logger.info("Fetching metrics for tweet %s", post_id)
        return {}
