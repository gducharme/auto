import os
from dotenv import load_dotenv, find_dotenv

DEFAULT_FEED_URL = "https://geoffreyducharme.substack.com/feed"

_loaded = False


def load_env() -> None:
    """Load environment variables from the nearest ``.env`` file once."""
    global _loaded
    if not _loaded:
        dotenv_path = find_dotenv()
        if dotenv_path:
            load_dotenv(dotenv_path)
        else:
            load_dotenv()
        _loaded = True


def get_database_url() -> str:
    load_env()
    return os.getenv("DATABASE_URL", "sqlite:///./substack.db")


def get_feed_url() -> str:
    load_env()
    return os.getenv("SUBSTACK_FEED_URL", DEFAULT_FEED_URL)


def get_mastodon_instance() -> str:
    load_env()
    return os.getenv("MASTODON_INSTANCE", "https://mastodon.social")


def get_mastodon_token() -> str | None:
    load_env()
    return os.getenv("MASTODON_TOKEN")


def get_poll_interval() -> int:
    load_env()
    return int(os.getenv("SCHEDULER_POLL_INTERVAL", "5"))


def get_ingest_interval() -> int:
    """Return the delay in seconds between automatic feed ingestions."""
    load_env()
    return int(os.getenv("INGEST_INTERVAL", "600"))


def get_post_delay() -> float:
    load_env()
    return float(os.getenv("POST_DELAY", "1"))


def get_max_attempts() -> int:
    load_env()
    return int(os.getenv("MAX_ATTEMPTS", "3"))


def get_medium_email() -> str | None:
    load_env()
    return os.getenv("MEDIUM_EMAIL")


def get_medium_password() -> str | None:
    load_env()
    return os.getenv("MEDIUM_PASSWORD")


def get_mastodon_sync_debug() -> bool:
    """Return True if debug output for Mastodon sync is enabled."""
    load_env()
    val = os.getenv("MASTODON_SYNC_DEBUG", "0").lower()
    return val not in {"0", "false", "no", "off", ""}
