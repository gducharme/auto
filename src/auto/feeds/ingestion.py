import sqlite3
import requests
from bs4 import BeautifulSoup
from alembic.config import Config
from alembic import command
from pathlib import Path

# Configuration
FEED_URL = 'https://geoffreyducharme.substack.com/feed'

# Determine project root four directories above this file
BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = str(BASE_DIR / 'substack.db')
ALEMBIC_INI = BASE_DIR / 'alembic.ini'


def init_db(db_path=DB_PATH):
    """Run database migrations to ensure the schema exists."""
    alembic_cfg = Config(str(ALEMBIC_INI))
    if db_path != DB_PATH:
        # If using a custom path, override the database URL
        url = db_path
        if not db_path.startswith("sqlite"):
            url = f"sqlite:///{db_path}"
        alembic_cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(alembic_cfg, "head")


def fetch_feed(feed_url=FEED_URL):
    """
    Fetch and parse the RSS feed using BeautifulSoup.
    Returns a list of parsed <item> elements.
    """
    response = requests.get(feed_url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "lxml")
    return soup.find_all("item")


def _parse_entry(item):
    """Return common fields extracted from a feed entry.

    The helper works with BeautifulSoup/feedparser elements as well as the
    simple dummy objects used in unit tests.
    """
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


def save_entries(items, db_path=DB_PATH):
    """Save new entries from the feed into the database.

    The function accepts either an iterable of parsed ``<item>`` elements or a
    feed object with an ``entries`` attribute.  Tests use a small dummy object so
    we support both real feedparser/BeautifulSoup objects and simple stubs.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Allow passing a feed object with an ``entries`` attribute
    items_iter = getattr(items, "entries", items)

    for item in items_iter:
        guid, title, link, summary, published = _parse_entry(item)

        try:
            c.execute(
                'INSERT INTO posts (id, title, link, summary, published) VALUES (?, ?, ?, ?, ?)',
                (guid, title, link, summary, published)
            )
            print(f"Saved post: {title}")
        except sqlite3.IntegrityError:
            # Duplicate entry, skip
            print(f"Skipping existing post: {title}")

    conn.commit()
    conn.close()


def main():
    init_db()
    items = fetch_feed()
    save_entries(items)


if __name__ == '__main__':
    main()

