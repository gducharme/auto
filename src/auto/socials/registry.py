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


_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    """Return the application's :class:`PluginRegistry` instance."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def reset_registry() -> None:
    """Clear the global registry (for tests)."""
    global _registry
    _registry = None

