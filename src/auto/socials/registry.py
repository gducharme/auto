from typing import Dict, Optional

from .base import SocialPlugin

_PLUGINS: Dict[str, SocialPlugin] = {}


def register_plugin(plugin: SocialPlugin) -> None:
    """Register a :class:`SocialPlugin` instance."""
    _PLUGINS[plugin.network] = plugin


def get_plugin(name: str) -> Optional[SocialPlugin]:
    """Return the plugin registered for ``name`` if any."""
    return _PLUGINS.get(name)


# register built-in plugins
from .mastodon_client import MastodonClient
from .medium_client import MediumClient

register_plugin(MastodonClient())
register_plugin(MediumClient())
