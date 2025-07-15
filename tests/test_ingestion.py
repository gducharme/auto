import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import create_engine
from auto.feeds.ingestion import init_db, save_entries

class DummyEntry:
    def __init__(self, id, title, link, summary="", published="", updated=""):
        self.id = id
        self.title = title
        self.link = link
        self.summary = summary
        self.published = published
        self.updated = updated

class DummyFeed:
    def __init__(self, entries):
        self.entries = entries


def test_save_entries_inserts_and_ignores_duplicates(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    init_db(str(db_path), engine=engine)

    feed = DummyFeed([
        DummyEntry(
            "1",
            "First",
            "http://example.com/1",
            published="2025-01-01",
            updated="2025-02-01",
        ),
        DummyEntry(
            "2",
            "Second",
            "http://example.com/2",
            published="2025-01-02",
            updated="2025-02-02",
        ),
    ])

    # First insertion
    save_entries(feed, str(db_path), engine=engine)
    # Duplicate run should not insert additional rows
    save_entries(feed, str(db_path), engine=engine)

    conn = sqlite3.connect(db_path)
    cur = conn.execute(
        "SELECT id, title, created_at, updated_at FROM posts ORDER BY id"
    )
    rows = cur.fetchall()
    conn.close()

    assert [r[:2] for r in rows] == [
        ("1", "First"),
        ("2", "Second"),
    ]
    assert all(r[2] is not None for r in rows)
    assert all(r[3] is not None for r in rows)
