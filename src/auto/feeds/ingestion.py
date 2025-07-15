import logging
import os
import requests
from typing import Optional
from bs4 import BeautifulSoup
from alembic.config import Config
from alembic import command
from dateutil import parser
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from ..db import SessionLocal

from ..models import Post

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_FEED_URL = "https://geoffreyducharme.substack.com/feed"


def get_feed_url() -> str:
    """Return the feed URL from ``SUBSTACK_FEED_URL`` or the default."""
    return os.getenv("SUBSTACK_FEED_URL", DEFAULT_FEED_URL)


# Determine project root four directories above this file
BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = str(BASE_DIR / "substack.db")
ALEMBIC_INI = BASE_DIR / "alembic.ini"


def _session_for_path(db_path: str, *, engine=None, session_factory=None):
    """Return a SQLAlchemy session for the given database path or engine."""
    if session_factory is not None:
        return session_factory()

    if engine is None:
        if db_path == DB_PATH:
            return SessionLocal()

        url = (
            db_path
            if db_path.startswith("sqlite") or "://" in db_path
            else f"sqlite:///{db_path}"
        )
        engine = create_engine(
            url,
            connect_args=(
                {"check_same_thread": False} if url.startswith("sqlite") else {}
            ),
        )

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()


def init_db(db_path=DB_PATH, *, engine=None, session_factory=None):
    """Run database migrations to ensure the schema exists."""
    alembic_cfg = Config(str(ALEMBIC_INI))

    bind = engine
    if bind is None and session_factory is not None:
        if isinstance(session_factory, sessionmaker):
            bind = session_factory.kw.get("bind")
        else:
            try:
                bind = session_factory().get_bind()
            finally:
                pass

    if bind is not None:
        alembic_cfg.attributes["connection"] = bind
    elif db_path != DB_PATH:
        url = db_path
        if not db_path.startswith("sqlite"):
            url = f"sqlite:///{db_path}"
        alembic_cfg.set_main_option("sqlalchemy.url", url)

    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc)
        raise


def fetch_feed(feed_url: Optional[str] = None):
    """Fetch and parse the RSS feed using BeautifulSoup."""
    if feed_url is None:
        feed_url = get_feed_url()
    try:
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch feed %s: %s", feed_url, exc)
        raise
    soup = BeautifulSoup(response.content, "xml")
    return soup.find_all("item")


def _parse_entry(item):
    """Return parsed fields extracted from a feed entry."""
    if callable(getattr(item, "findtext", None)):
        guid = item.findtext("guid") or item.findtext("id") or item.findtext("link")
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        summary = item.findtext("description", "")
        published = item.findtext("pubDate", "")
        updated = item.findtext("updated") or item.findtext("updated_at", "")
    elif hasattr(item, "find"):

        def _text(tag_name, default=""):
            el = item.find(tag_name)
            return el.get_text() if el else default

        guid = _text("guid") or _text("id") or _text("link")
        title = _text("title")
        link = _text("link")
        summary = _text("description")
        published = _text("pubDate")
        updated = _text("updated") or _text("updated_at")
    else:
        guid = getattr(item, "id", getattr(item, "link", ""))
        title = getattr(item, "title", "")
        link = getattr(item, "link", "")
        summary = getattr(item, "summary", "")
        published = getattr(item, "published", "")
        updated = getattr(item, "updated", getattr(item, "updated_at", ""))

    created_dt = None
    updated_dt = None
    if published:
        try:
            created_dt = parser.parse(published)
        except Exception:
            pass
    if updated:
        try:
            updated_dt = parser.parse(updated)
        except Exception:
            pass

    return guid, title, link, summary, published, created_dt, updated_dt


def save_entries(items, db_path=DB_PATH, *, engine=None, session_factory=None):
    """Save new entries from the feed into the database."""
    session = _session_for_path(db_path, engine=engine, session_factory=session_factory)

    items_iter = getattr(items, "entries", items)

    try:
        with session.begin():
            for item in items_iter:
                guid, title, link, summary, published, created_dt, updated_dt = (
                    _parse_entry(item)
                )

                post = Post(
                    id=guid,
                    title=title,
                    link=link,
                    summary=summary,
                    published=published,
                    created_at=created_dt,
                    updated_at=updated_dt,
                )

                try:
                    with session.begin_nested():
                        session.add(post)
                        session.flush()
                    logger.info("Saved post: %s", title)
                except IntegrityError:
                    logger.info("Skipping existing post: %s", title)
                except Exception as exc:
                    logger.error("Failed to save post %s: %s", title, exc)
    finally:
        session.close()


def main():
    init_db()
    items = fetch_feed()
    save_entries(items)


if __name__ == "__main__":
    main()
