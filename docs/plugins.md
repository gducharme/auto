# Writing Social Network Plugins

Auto supports pluggable social network clients. Plugins implement the
`SocialPlugin` protocol and register an instance in
`src/auto/socials/registry.py`.

## Creating a Plugin

1. Add a module under `src/auto/socials/` that defines a class with
   a ``network`` attribute and ``post()`` and ``fetch_metrics()`` methods.
2. Import your class in `src/auto/socials/registry.py` and call
   ``register_plugin(MyPlugin())``.

The ``network`` string identifies the plugin when Auto publishes posts.

Our guidelines avoid using Selenium for browser automation. Instead, use the
[`SafariController`](../src/auto/automation/safari.py) helper shown below.

## Example: MediumClient

```python
from __future__ import annotations
import asyncio
import logging
from typing import Dict
from auto.automation.safari import SafariController

from .base import SocialPlugin

logger = logging.getLogger(__name__)

class MediumClient(SocialPlugin):
    network = "medium"

    def __init__(self, safari: SafariController | None = None) -> None:
        self.safari = safari or SafariController()

    async def post(self, text: str, visibility: str = "draft") -> None:
        await asyncio.to_thread(self._post_sync, text, visibility)

    def _post_sync(self, text: str, visibility: str) -> None:
        from ..automation.medium import MediumClient as AutomationClient

        safari = self.safari or SafariController()
        client = AutomationClient(safari=safari)
        try:
            client.login()
            safari.open("https://medium.com/new-story")
            safari.fill("article", text)
            logger.info("Created Medium draft")
        finally:
            client.close()

    async def fetch_metrics(self, post_id: str) -> Dict[str, int]:
        logger.info("MediumClient.fetch_metrics called for %s", post_id)
        return {}
```

After defining the class, update `src/auto/socials/registry.py`:

```python
from .mastodon_client import MastodonClient
from .medium_client import MediumClient

register_plugin(MastodonClient())
register_plugin(MediumClient())
```

Auto will then be able to publish posts to Medium using this plugin.
