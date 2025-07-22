import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup
from tests.helpers import DummyResponse


import auto.main as main
from sqlalchemy import create_engine
from auto.feeds import ingestion


def test_ingest_endpoint(tmp_path, monkeypatch):
    sample_xml = Path(__file__).with_name("sample_feed.xml").read_bytes()
    parsed = BeautifulSoup(sample_xml, "xml").find_all("item")

    async def fake_fetch_feed(url=None):
        return parsed

    monkeypatch.setattr(ingestion, "fetch_feed_async", fake_fetch_feed)

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
    monkeypatch.setattr(main, "init_db", init_db_patch)

    with TestClient(main.app) as client:
        resp = client.post("/ingest")
        assert resp.status_code == 200

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT content FROM posts ORDER BY id").fetchall()
    conn.close()

    assert len(rows) == len(parsed)
    assert all(r[0] is not None and r[0] != "" for r in rows)


def test_run_ingest_uses_env_variable(monkeypatch):
    """run_ingest() should fetch the URL from SUBSTACK_FEED_URL."""
    monkeypatch.setenv("SUBSTACK_FEED_URL", "http://env.example/feed")

    import auto.feeds.ingestion as ingest_module

    called = {}

    async def fake_get(self, url):
        called["url"] = url
        return DummyResponse()

    monkeypatch.setattr("auto.feeds.ingestion.httpx.AsyncClient.get", fake_get)
    monkeypatch.setattr(ingest_module, "save_entries", lambda items: None)

    ingest_module.run_ingest()
    assert called.get("url") == "http://env.example/feed"


def test_ingest_endpoint_propagates_errors(monkeypatch):
    def fail_ingest():
        raise RuntimeError("boom")

    monkeypatch.setattr(main, "run_ingest", fail_ingest)

    with TestClient(main.app) as client:
        resp = client.post("/ingest")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "ingestion failed"
