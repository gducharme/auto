import sqlite3
import feedparser
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
    command.upgrade(alembic_cfg, "head")


def fetch_feed(feed_url=FEED_URL):
    """
    Fetch and parse the RSS feed, returning the parsed feed object.
    """
    return feedparser.parse(feed_url)


def save_entries(feed, db_path=DB_PATH):
    """
    Save new entries from the feed into the database.
    Avoid duplicates by primary key.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for entry in feed.entries:
        # Use entry.id if available, else fallback to link
        guid = getattr(entry, 'id', entry.link)
        title = entry.title
        link = entry.link
        summary = getattr(entry, 'summary', '')
        published = getattr(entry, 'published', '')

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
    feed = fetch_feed()
    save_entries(feed)


if __name__ == '__main__':
    main()

