import asyncio
import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from alembic.config import Config
from alembic import command
from dateutil import parser
from pathlib import Path

from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from ..db import SessionLocal

from ..models import Post
from ..config import load_env, get_feed_url
logger = logging.getLogger(__name__)



# Determine project root four directories above this file
BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = str(BASE_DIR / "substack.db")
ALEMBIC_INI = BASE_DIR / "alembic.ini"


def _session_for_path(db_path: str, *, engine=None, session_factory=None):
    """Return a SQLAlchemy session for the given database path or engine."""
    if session_factory is not None:
        return session_factory()

    if engine is None:
        return SessionLocal()

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


async def fetch_feed_async(feed_url: Optional[str] = None):
    """Fetch and parse the RSS feed asynchronously."""
    if feed_url is None:
        feed_url = get_feed_url()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(feed_url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch feed %s: %s", feed_url, exc)
        raise
    soup = BeautifulSoup(response.content, "xml")
    return soup.find_all("item")


def fetch_feed(feed_url: Optional[str] = None):
    """Synchronous wrapper around :func:`fetch_feed_async`."""
    return asyncio.run(fetch_feed_async(feed_url))


def _extract_text(item, name: str, default: str = ""):
    """Return the value for ``name`` from a feed item regardless of its type."""
    if callable(getattr(item, "findtext", None)):
        return item.findtext(name, default)
    if hasattr(item, "find"):
        el = item.find(name)
        return el.get_text() if el else default
    return getattr(item, name, default)


def _parse_entry(item):
    """Return parsed fields extracted from a feed entry."""

    def get(field, default=""):
        """Convenience wrapper around ``_extract_text`` for ``item``."""
        return _extract_text(item, field, default)

    guid = get("guid") or get("id") or get("link")
    title = get("title")
    link = get("link")
    summary = get("description") or get("summary")
    published = get("pubDate") or get("published")
    updated = get("updated") or get("updated_at")

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
    items_iter = getattr(items, "entries", items)

    with _session_for_path(db_path, engine=engine, session_factory=session_factory) as session:
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


async def run_ingest_async() -> None:
    """Fetch the configured feed and store any new entries asynchronously."""
    try:
        items = await fetch_feed_async()
        save_entries(items)
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)


def run_ingest() -> None:
    """Synchronous wrapper around :func:`run_ingest_async`."""
    asyncio.run(run_ingest_async())


def main():
    init_db()
    asyncio.run(run_ingest_async())


if __name__ == "__main__":
    main()
