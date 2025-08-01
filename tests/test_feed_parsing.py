from pathlib import Path
from types import SimpleNamespace

from bs4 import BeautifulSoup
from dateutil import parser
from auto.feeds.ingestion import _parse_entry, fetch_feed
from tests.helpers import DummyResponse


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
        "",
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
        "",
        "2025-01-01",
        parser.parse("2025-01-01"),
        parser.parse("2025-02-01"),
    )


def test_fetch_feed_returns_items(monkeypatch):
    sample_xml = Path(__file__).with_name("sample_feed.xml").read_bytes()

    async def fake_get(self, url):
        return DummyResponse(sample_xml)

    monkeypatch.setattr("auto.feeds.ingestion.httpx.AsyncClient.get", fake_get)

    items = fetch_feed("http://example.com/feed")
    assert isinstance(items, list)
    assert all(item.name == "item" for item in items)


def test_fetch_feed_uses_env_variable(monkeypatch):
    """fetch_feed() should use SUBSTACK_FEED_URL when no URL is provided."""
    monkeypatch.setenv("SUBSTACK_FEED_URL", "http://env.example/feed")

    called = {}

    async def fake_get(self, url):
        called["url"] = url
        return DummyResponse()

    monkeypatch.setattr("auto.feeds.ingestion.httpx.AsyncClient.get", fake_get)

    from auto.feeds import ingestion as ingestion_module

    ingestion_module.fetch_feed()
    assert called.get("url") == "http://env.example/feed"
