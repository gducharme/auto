class DummyResponse:
    """Simple mock response for requests.get."""

    def __init__(self, content=b"<rss></rss>", status_code=200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        """Pretend to raise for HTTP errors."""
        pass
