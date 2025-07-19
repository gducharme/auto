from __future__ import annotations

import asyncio
import logging
from typing import Dict

from ..automation.safari import SafariController

from .base import SocialPlugin

logger = logging.getLogger(__name__)


class MediumClient(SocialPlugin):
    """SocialPlugin implementation using the Safari automation client."""

    network = "medium"

    def __init__(self, safari: SafariController | None = None) -> None:
        self.safari = safari

    async def post(self, text: str, visibility: str = "draft") -> None:
        """Publish ``text`` as a new Medium draft."""

        await asyncio.to_thread(self._post_sync, text, visibility)

    def _post_sync(self, text: str, visibility: str) -> None:
        from ..automation.medium import MediumClient as AutomationClient

        safari = self.safari or SafariController()
        client = AutomationClient(safari=safari)
        try:
            client.login()
            safari.open("https://medium.com/new-story")
            safari.fill("body", text)
            logger.info("Created Medium draft")
        finally:
            client.close()

    async def fetch_metrics(self, post_id: str) -> Dict[str, int]:
        logger.info("MediumClient.fetch_metrics called for %s", post_id)
        return {}
