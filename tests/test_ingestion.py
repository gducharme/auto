import sqlite3
from types import SimpleNamespace
from unittest.mock import patch
import sys
from pathlib import Path

import pytest

# Allow importing the package from the src directory without installation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auto.feeds.ingestion import fetch_feed, save_entries, FEED_URL


def setup_db(path: str) -> None:
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE posts (id TEXT PRIMARY KEY, title TEXT NOT NULL, link TEXT NOT NULL, summary TEXT, published TEXT)"
    )
    conn.commit()
    conn.close()


def test_fetch_feed_uses_feedparser_parse():
    expected = object()
    with patch("auto.feeds.ingestion.feedparser.parse", return_value=expected) as mock_parse:
        result = fetch_feed()
        mock_parse.assert_called_once_with(FEED_URL)
        assert result is expected


def test_save_entries_inserts_and_skips_duplicates(tmp_path):
    db_file = tmp_path / "test.db"
    setup_db(str(db_file))

    entry1 = SimpleNamespace(id="1", title="t1", link="http://example.com/1", summary="s1", published="p1")
    entry2 = SimpleNamespace(id="2", title="t2", link="http://example.com/2", summary="s2", published="p2")
    feed = SimpleNamespace(entries=[entry1, entry2])

    # initial insert
    save_entries(feed, db_path=str(db_file))

    conn = sqlite3.connect(str(db_file))
    c = conn.cursor()
    c.execute("SELECT id FROM posts ORDER BY id")
    rows = c.fetchall()
    conn.close()
    assert rows == [("1",), ("2",)]

    # duplicate insert should not raise and should be ignored
    save_entries(feed, db_path=str(db_file))

    conn = sqlite3.connect(str(db_file))
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posts")
    count = c.fetchone()[0]
    conn.close()
    assert count == 2
