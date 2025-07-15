import logging
import requests
from bs4 import BeautifulSoup
from alembic.config import Config
from alembic import command
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from ..db import SessionLocal, DATABASE_URL

from ..models import Post

logger = logging.getLogger(__name__)

# Configuration
FEED_URL = 'https://geoffreyducharme.substack.com/feed'

# Determine project root four directories above this file
BASE_DIR = Path(__file__).resolve().parents[3]
ALEMBIC_INI = BASE_DIR / 'alembic.ini'

# Default database URL from the main db module
DEFAULT_DB_URL = DATABASE_URL


def _session_for_url(db_url: str = DEFAULT_DB_URL):
    """Return a SQLAlchemy session for the given database URL."""
    if not db_url or db_url == DEFAULT_DB_URL:
        return SessionLocal()

    url = db_url if db_url.startswith("sqlite") or "://" in db_url else f"sqlite:///{db_url}"
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    )
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def init_db(db_url=DEFAULT_DB_URL):
    """Run database migrations to ensure the schema exists."""
    alembic_cfg = Config(str(ALEMBIC_INI))
    if db_url != DEFAULT_DB_URL:
        url = db_url
        if not db_url.startswith("sqlite") and "://" not in db_url:
            url = f"sqlite:///{db_url}"
        alembic_cfg.set_main_option("sqlalchemy.url", url)
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc)
        raise


def fetch_feed(feed_url=FEED_URL):
    """Fetch and parse the RSS feed using BeautifulSoup."""
    try:
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch feed %s: %s", feed_url, exc)
        raise
    soup = BeautifulSoup(response.content, "lxml")
    return soup.find_all("item")


def _parse_entry(item):
    """Return common fields extracted from a feed entry."""
    if callable(getattr(item, "findtext", None)):
        guid = item.findtext("guid") or item.findtext("id") or item.findtext("link")
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        summary = item.findtext("description", "")
        published = item.findtext("pubDate", "")
    elif hasattr(item, "find"):
        def _text(tag_name, default=""):
            el = item.find(tag_name)
            return el.get_text() if el else default

        guid = _text("guid") or _text("id") or _text("link")
        title = _text("title")
        link = _text("link")
        summary = _text("description")
        published = _text("pubDate")
    else:
        guid = getattr(item, "id", getattr(item, "link", ""))
        title = getattr(item, "title", "")
        link = getattr(item, "link", "")
        summary = getattr(item, "summary", "")
        published = getattr(item, "published", "")

    return guid, title, link, summary, published


def save_entries(items, db_url=DEFAULT_DB_URL):
    """Save new entries from the feed into the database."""
    session = _session_for_url(db_url)

    items_iter = getattr(items, "entries", items)

    for item in items_iter:
        guid, title, link, summary, published = _parse_entry(item)
        post = Post(id=guid, title=title, link=link, summary=summary, published=published)
        session.add(post)
        try:
            session.commit()
            logger.info("Saved post: %s", title)
        except IntegrityError:
            session.rollback()
            logger.info("Skipping existing post: %s", title)
        except Exception as exc:
            session.rollback()
            logger.error("Failed to save post %s: %s", title, exc)

    session.close()


def main():
    init_db()
    items = fetch_feed()
    save_entries(items)


if __name__ == '__main__':
    main()
