import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)


def _get_credentials():
    """Return Medium login credentials from the environment."""
    email = os.getenv("MEDIUM_EMAIL")
    password = os.getenv("MEDIUM_PASSWORD")
    if not email or not password:
        raise ValueError("MEDIUM_EMAIL and MEDIUM_PASSWORD must be set")
    return email, password


class MediumClient:
    """Automate basic Medium interactions using Selenium."""

    def __init__(self, driver: webdriver.Firefox | None = None) -> None:
        self.driver = driver or webdriver.Firefox()

    def login(self) -> None:
        """Sign in to Medium using credentials from the environment."""
        email, password = _get_credentials()
        try:
            self.driver.get("https://medium.com/m/signin")
            email_input = self.driver.find_element(By.NAME, "email")
            email_input.send_keys(email)
            email_input.send_keys(Keys.RETURN)
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(password)
            password_input.send_keys(Keys.RETURN)
            logger.info("Submitted Medium login form")
        except Exception as exc:
            logger.error("Failed to sign in to Medium: %s", exc)
            raise

    def close(self) -> None:
        self.driver.quit()
