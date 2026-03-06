import os
from dotenv import load_dotenv, find_dotenv
from typing import Optional

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


def get_mastodon_token() -> Optional[str]:
    load_env()
    return os.getenv("MASTODON_TOKEN")


def get_poll_interval() -> int:
    load_env()
    return int(os.getenv("SCHEDULER_POLL_INTERVAL", "5"))


def get_ingest_interval() -> int:
    """Return the delay in seconds between automatic feed ingestions."""
    load_env()
    return int(os.getenv("INGEST_INTERVAL", "600"))


def get_replay_check_interval() -> int:
    """Return the delay in seconds between replay status scans."""
    load_env()
    return int(os.getenv("REPLAY_CHECK_INTERVAL", "3600"))


def get_post_delay() -> float:
    load_env()
    return float(os.getenv("POST_DELAY", "1"))


def get_max_attempts() -> int:
    load_env()
    return int(os.getenv("MAX_ATTEMPTS", "3"))


def get_medium_email() -> Optional[str]:
    load_env()
    return os.getenv("MEDIUM_EMAIL")


def get_medium_password() -> Optional[str]:
    load_env()
    return os.getenv("MEDIUM_PASSWORD")


def get_mastodon_sync_debug() -> bool:
    """Return True if debug output for Mastodon sync is enabled."""
    load_env()
    val = os.getenv("MASTODON_SYNC_DEBUG", "0").lower()
    return val not in {"0", "false", "no", "off", ""}


def _env_flag(name: str, default: str = "0") -> bool:
    load_env()
    value = os.getenv(name, default).strip().lower()
    return value not in {"0", "false", "no", "off", ""}


def get_instagram_pipeline_enabled() -> bool:
    return _env_flag("INSTAGRAM_PIPELINE_ENABLED", "1")


def get_instagram_pipeline_auto_publish() -> bool:
    return _env_flag("INSTAGRAM_PIPELINE_AUTO_PUBLISH", "0")


def get_instagram_pipeline_quality_threshold() -> float:
    load_env()
    return float(os.getenv("INSTAGRAM_PIPELINE_QUALITY_THRESHOLD", "0.75"))


def get_instagram_pipeline_banned_terms() -> set[str]:
    load_env()
    raw = os.getenv("INSTAGRAM_PIPELINE_BANNED_TERMS", "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def get_instagram_pipeline_export_enabled() -> bool:
    return _env_flag("INSTAGRAM_PIPELINE_EXPORT_ENABLED", "1")


def get_instagram_pipeline_export_dir() -> str:
    load_env()
    return os.getenv("INSTAGRAM_PIPELINE_EXPORT_DIR", "artifacts/instagram_pipeline")
