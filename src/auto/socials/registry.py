from typing import Dict, Optional

from .base import SocialPlugin


class PluginRegistry:
    """Container for :class:`SocialPlugin` instances."""

    def __init__(self) -> None:
        self._plugins: Dict[str, SocialPlugin] = {}

    def register(self, plugin: SocialPlugin) -> None:
        """Register ``plugin`` under its ``network`` name."""
        self._plugins[plugin.network] = plugin

    def get(self, name: str) -> Optional[SocialPlugin]:
        """Return the plugin registered for ``name`` if any."""
        return self._plugins.get(name)


# Global reference to the application's plugin registry. It is created during
# application startup.
plugins: PluginRegistry | None = None
