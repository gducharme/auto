from mastodon import Mastodon
import logging

from ..config import get_mastodon_instance, get_mastodon_token

logger = logging.getLogger(__name__)


def post_to_mastodon(status: str, visibility: str = "private") -> None:
    """Post a status to Mastodon."""
    try:
        masto = Mastodon(
            access_token=get_mastodon_token(),
            api_base_url=get_mastodon_instance(),
        )
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
