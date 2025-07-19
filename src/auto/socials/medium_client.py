from __future__ import annotations

import asyncio
import logging
from typing import Dict

from selenium import webdriver
from selenium.webdriver.common.by import By

from .base import SocialPlugin
from .registry import register_plugin

logger = logging.getLogger(__name__)


class MediumClient(SocialPlugin):
    """SocialPlugin implementation using the Selenium automation client."""

    network = "medium"

    def __init__(self, driver: webdriver.Firefox | None = None) -> None:
        self.driver = driver

    async def post(self, text: str, visibility: str = "draft") -> None:
        """Publish ``text`` as a new Medium draft."""

        await asyncio.to_thread(self._post_sync, text, visibility)

    def _post_sync(self, text: str, visibility: str) -> None:
        from ..automation.medium import MediumClient as AutomationClient

        driver = self.driver or webdriver.Firefox()
        client = AutomationClient(driver=driver)
        try:
            client.login()
            driver.get("https://medium.com/new-story")
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(text)
            logger.info("Created Medium draft")
        finally:
            client.close()

    async def fetch_metrics(self, post_id: str) -> Dict[str, int]:
        logger.info("MediumClient.fetch_metrics called for %s", post_id)
        return {}


register_plugin(MediumClient())
