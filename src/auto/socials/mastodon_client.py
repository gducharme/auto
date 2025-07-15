from mastodon import Mastodon
from dotenv import load_dotenv
from pathlib import Path
import logging
import os

# Load environment variables from the project root .env file
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

MASTODON_INSTANCE = os.getenv("MASTODON_INSTANCE", "https://mastodon.social")
ACCESS_TOKEN = os.getenv("MASTODON_TOKEN")

logger = logging.getLogger(__name__)


def post_to_mastodon(status: str, visibility: str = "private") -> None:
    """Post a status to Mastodon."""
    try:
        masto = Mastodon(access_token=ACCESS_TOKEN, api_base_url=MASTODON_INSTANCE)
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
