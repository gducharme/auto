from mastodon import Mastodon
from dotenv import load_dotenv, find_dotenv
import logging
import os

logger = logging.getLogger(__name__)


def _load_env() -> None:
    """Load environment variables from the nearest ``.env`` file."""
    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path)


def get_instance() -> str:
    """Return the Mastodon instance URL."""
    _load_env()
    return os.getenv("MASTODON_INSTANCE", "https://mastodon.social")


def get_access_token() -> str:
    """Return the Mastodon access token."""
    _load_env()
    return os.getenv("MASTODON_TOKEN")


def post_to_mastodon(status: str, visibility: str = "private") -> None:
    """Post a status to Mastodon."""
    try:
        masto = Mastodon(access_token=get_access_token(), api_base_url=get_instance())
        # `toot` in Mastodon.py 2.x does not accept extra keyword arguments such as
        # ``visibility``.  Use ``status_post`` instead, which exposes these
        # parameters.
        masto.status_post(status=status, visibility=visibility)
        logger.info("Posted to Mastodon")
    except Exception as exc:
        logger.error("Failed to post to Mastodon: %s", exc)
        raise


if __name__ == "__main__":
    post_to_mastodon("Hello world! My Substack → Socials bot is live 🚀")
