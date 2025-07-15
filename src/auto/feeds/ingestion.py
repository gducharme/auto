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
    command.upgrade(alembic_cfg, "head")


def fetch_feed(feed_url=FEED_URL):
    """
    Fetch and parse the RSS feed using BeautifulSoup.
    Returns a list of parsed <item> elements.
    """
    response = requests.get(feed_url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "xml")
    return soup.find_all("item")


def save_entries(items, db_path=DB_PATH):
    """
    Save new entries from the feed into the database.
    Avoid duplicates by primary key.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for item in items:
        guid = item.findtext("guid") or item.findtext("id") or item.findtext("link")
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        summary = item.findtext("description", "")
        published = item.findtext("pubDate", "")

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

