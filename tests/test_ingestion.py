import sqlite3
from types import SimpleNamespace

import feedparser
import pytest

from auto.feeds.ingestion import fetch_feed, save_entries, FEED_URL


def make_db(path: str):
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE posts (id TEXT PRIMARY KEY, title TEXT, link TEXT, summary TEXT, published TEXT)"
    )
    conn.commit()
    conn.close()


def test_fetch_feed_wraps_feedparser_parse(monkeypatch):
    returned = {"url": None}

    def fake_parse(url):
        returned["url"] = url
        return {"parsed": True}

    monkeypatch.setattr(feedparser, "parse", fake_parse)
    result = fetch_feed()
    assert returned["url"] == FEED_URL
    assert result == {"parsed": True}


def test_save_entries_saves_new_and_skips_duplicates(tmp_path):
    db_path = tmp_path / "db.sqlite"
    make_db(str(db_path))

    e1 = SimpleNamespace(id="1", title="A", link="la", summary="", published="")
    e2 = SimpleNamespace(id="2", title="B", link="lb", summary="", published="")

    # first call with duplicate within feed
    feed1 = SimpleNamespace(entries=[e1, e1])
    save_entries(feed1, db_path=str(db_path))

    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    assert count == 1
    conn.close()

    # second call with existing and new entry
    feed2 = SimpleNamespace(entries=[e1, e2])
    save_entries(feed2, db_path=str(db_path))

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, title FROM posts ORDER BY id").fetchall()
    conn.close()
    assert rows == [("1", "A"), ("2", "B")]
