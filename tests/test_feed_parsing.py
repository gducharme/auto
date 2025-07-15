import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bs4 import BeautifulSoup
import requests
from dateutil import parser
from auto.feeds.ingestion import _parse_entry, fetch_feed


def test_parse_entry_from_soup():
    xml = (
        "<item>"
        "<guid>123</guid>"
        "<title>Example</title>"
        "<link>http://example.com</link>"
        "<description>Summary</description>"
        "<pubDate>Mon, 01 Jan 2000 00:00:00 +0000</pubDate>"
        "</item>"
    )
    item = BeautifulSoup(xml, "xml").find("item")
    result = _parse_entry(item)
    assert result == (
        "123",
        "Example",
        "http://example.com",
        "Summary",
        "Mon, 01 Jan 2000 00:00:00 +0000",
        parser.parse("Mon, 01 Jan 2000 00:00:00 +0000"),
        None,
    )


def test_parse_entry_from_dummy_object():
    dummy = SimpleNamespace(
        id="1",
        title="Dummy",
        link="http://dummy",
        summary="Body",
        published="2025-01-01",
        updated="2025-02-01",
    )
    result = _parse_entry(dummy)
    assert result == (
        "1",
        "Dummy",
        "http://dummy",
        "Body",
        "2025-01-01",
        parser.parse("2025-01-01"),
        parser.parse("2025-02-01"),
    )


def test_fetch_feed_returns_items(monkeypatch):
    sample_xml = Path(__file__).with_name("sample_feed.xml").read_bytes()

    class DummyResponse:
        def __init__(self, content):
            self.content = content
            self.status_code = 200

        def raise_for_status(self):
            pass

    def fake_get(url, timeout=10):
        return DummyResponse(sample_xml)

    monkeypatch.setattr("requests.get", fake_get)

    items = fetch_feed("http://example.com/feed")
    assert isinstance(items, list)
    assert all(item.name == "item" for item in items)


def test_fetch_feed_uses_env_variable(monkeypatch):
    """fetch_feed() should use SUBSTACK_FEED_URL when no URL is provided."""
    monkeypatch.setenv("SUBSTACK_FEED_URL", "http://env.example/feed")
    # reload module so FEED_URL picks up env var
    import importlib
    import auto.feeds.ingestion as ingestion_module
    importlib.reload(ingestion_module)

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

    monkeypatch.setattr(ingestion_module.requests, "get", fake_get)

    ingestion_module.fetch_feed()
    assert called.get("url") == "http://env.example/feed"

