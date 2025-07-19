import logging
from typing import Dict

from .base import SocialPlugin
from .registry import register_plugin

logger = logging.getLogger(__name__)


class MediumClient(SocialPlugin):
    """Placeholder SocialPlugin implementation for Medium."""

    network = "medium"

    async def post(self, text: str, visibility: str = "draft") -> None:
        logger.info("MediumClient.post called with %s", text)
        # TODO: implement real posting logic

    async def fetch_metrics(self, post_id: str) -> Dict[str, int]:
        logger.info("MediumClient.fetch_metrics called for %s", post_id)
        return {}


register_plugin(MediumClient())
