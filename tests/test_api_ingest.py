import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup


import auto.main as main
from sqlalchemy import create_engine
from auto.feeds import ingestion


def test_ingest_endpoint(tmp_path, monkeypatch):
    sample_xml = Path(__file__).with_name("sample_feed.xml").read_bytes()
    parsed = BeautifulSoup(sample_xml, "xml").find_all("item")

    monkeypatch.setattr(ingestion, "fetch_feed", lambda url=None: parsed)
    monkeypatch.setattr(main, "fetch_feed", lambda url=None: parsed)

    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )

    orig_init_db = ingestion.init_db
    orig_save_entries = ingestion.save_entries

    def init_db_patch(path=str(db_path)):
        return orig_init_db(str(db_path), engine=engine)

    def save_entries_patch(items, path=str(db_path)):
        return orig_save_entries(items, str(db_path), engine=engine)

    monkeypatch.setattr(ingestion, "init_db", init_db_patch)
    monkeypatch.setattr(ingestion, "save_entries", save_entries_patch)
    monkeypatch.setattr(main, "save_entries", save_entries_patch)
    monkeypatch.setattr(main, "init_db", init_db_patch)

    with TestClient(main.app) as client:
        resp = client.post("/ingest")
        assert resp.status_code == 200

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT created_at, updated_at FROM posts").fetchall()
    conn.close()

    assert len(rows) == len(parsed)
    assert all(r[0] is not None for r in rows)


def test_run_ingest_uses_env_variable(monkeypatch):
    """run_ingest() should fetch the URL from SUBSTACK_FEED_URL."""
    monkeypatch.setenv("SUBSTACK_FEED_URL", "http://env.example/feed")

    import auto.main as main_module

    called = {}

    class DummyResponse:
        def __init__(self):
            self.content = b"<rss></rss>"
            self.status_code = 200

        def raise_for_status(self):
            pass

    def fake_get(url, timeout=10):
        called["url"] = url
        return DummyResponse()

    monkeypatch.setattr("auto.feeds.ingestion.requests.get", fake_get)
    monkeypatch.setattr(main_module, "save_entries", lambda items: None)

    main_module.run_ingest()
    assert called.get("url") == "http://env.example/feed"
