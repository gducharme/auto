import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auto.feeds.ingestion import init_db, save_entries

class DummyEntry:
    def __init__(self, id, title, link, summary="", published=""):
        self.id = id
        self.title = title
        self.link = link
        self.summary = summary
        self.published = published

class DummyFeed:
    def __init__(self, entries):
        self.entries = entries


def test_save_entries_inserts_and_ignores_duplicates(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(str(db_path))

    feed = DummyFeed([
        DummyEntry("1", "First", "http://example.com/1"),
        DummyEntry("2", "Second", "http://example.com/2"),
    ])

    # First insertion
    save_entries(feed, str(db_path))
    # Duplicate run should not insert additional rows
    save_entries(feed, str(db_path))

    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT id, title FROM posts ORDER BY id")
    rows = cur.fetchall()
    conn.close()

    assert rows == [
        ("1", "First"),
        ("2", "Second"),
    ]
