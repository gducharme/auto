import asyncio
import logging
from selenium.webdriver.common.by import By

from ..automation.medium import MediumClient

logger = logging.getLogger(__name__)


def _post_to_medium(title: str, content: str) -> None:
    client = MediumClient()
    try:
        client.login()
        client.driver.get("https://medium.com/new-story")
        title_el = client.driver.find_element(By.TAG_NAME, "h1")
        title_el.send_keys(title)
        body_el = client.driver.find_element(By.CSS_SELECTOR, "article")
        body_el.click()
        body_el.send_keys(content)
        publish_btn = client.driver.find_element(
            By.XPATH, "//span[contains(text(),'Publish')]"
        )
        publish_btn.click()
        logger.info("Posted to Medium")
    finally:
        client.close()


async def post_to_medium_async(title: str, content: str) -> None:
    """Publish ``content`` on Medium with ``title``."""
    try:
        await asyncio.to_thread(_post_to_medium, title, content)
    except Exception as exc:
        logger.error("Failed to post to Medium: %s", exc)
        raise
