from typing import Protocol, Dict


class SocialPlugin(Protocol):
    """Interface for social network plugins."""

    network: str

    async def post(self, text: str, visibility: str = "unlisted") -> None:
        """Publish ``text`` to the network."""

    async def fetch_metrics(self, post_id: str) -> Dict[str, int]:
        """Return engagement metrics for ``post_id``."""
