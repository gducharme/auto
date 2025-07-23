from __future__ import annotations

import asyncio
import json
from typing import Dict

from jinja2 import Template

from ..automation.safari import SafariController
from ..utils import project_root
from .base import SocialPlugin


class TwitterClient(SocialPlugin):
    """SocialPlugin implementation using Safari automation."""

    network = "twitter"

    def __init__(self, safari: SafariController | None = None) -> None:
        self.safari = safari or SafariController()
        commands_path = (
            project_root() / "tests" / "fixtures" / "twitter" / "commands.json"
        )
        self.commands: list[list[str]] = json.loads(commands_path.read_text())

    async def post(self, text: str, visibility: str = "unlisted") -> None:
        await asyncio.to_thread(self._run_commands, text)

    def _run_commands(self, text: str) -> None:
        for entry in self.commands:
            cmd = entry[0]
            args = [Template(arg).render(tweet=text) for arg in entry[1:]]
            if cmd == "open" and args:
                self.safari.open(args[0])
            elif cmd == "click" and args:
                self.safari.click(args[0])
            elif cmd == "fill" and len(args) == 2:
                self.safari.fill(args[0], args[1])
            elif cmd == "run_js" and args:
                self.safari.run_js(args[0])
            elif cmd == "run_js_file" and args:
                path = project_root() / args[0]
                if path.exists():
                    self.safari.run_js(path.read_text())
            elif cmd == "close_tab":
                self.safari.close_tab()
            # ignore unsupported commands like fetch_dom

    async def fetch_metrics(self, post_id: str) -> Dict[str, int]:
        return {}
