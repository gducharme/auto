import logging

from .safari import SafariController

from ..config import get_medium_email, get_medium_password

logger = logging.getLogger(__name__)


def _get_credentials():
    """Return Medium login credentials from the environment."""
    email = get_medium_email()
    password = get_medium_password()
    if not email or not password:
        raise ValueError("MEDIUM_EMAIL and MEDIUM_PASSWORD must be set")
    return email, password


class MediumClient:
    """Automate basic Medium interactions using ``SafariController``."""

    def __init__(self, safari: SafariController | None = None) -> None:
        self.safari = safari or SafariController()

    def login(self) -> None:
        """Sign in to Medium using credentials from the environment."""
        email, password = _get_credentials()
        try:
            self.safari.open("https://medium.com/m/signin")
            self.safari.fill("input[name='email']", email)
            self.safari.fill("input[name='password']", password)
            self.safari.click("button[type='submit']")
            logger.info("Submitted Medium login form")
        except Exception as exc:
            logger.error("Failed to sign in to Medium: %s", exc)
            raise

    def close(self) -> None:
        self.safari.close_tab()
