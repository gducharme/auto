"""Replay recorded Safari automation fixtures."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Optional

from jinja2 import Template

from ..db import SessionLocal
from ..models import PostPreview, Post, PostStatus
from ..cli.helpers import _slow_print
from ..html_helpers import fetch_dom as fetch_dom_html
from .safari import SafariController

logger = logging.getLogger(__name__)


def replay_fixture(
    name: str, post_id: Optional[str] = None, network: str = "mastodon"
) -> None:
    """Replay commands from ``tests/fixtures/<name>/commands.json``."""

    fixtures_root = Path("tests/fixtures")
    commands_path = fixtures_root / name / "commands.json"
    if not commands_path.exists():
        raise FileNotFoundError(f"commands.json not found: {commands_path}")

    commands: list[list[str]] = json.loads(commands_path.read_text())

    controller = SafariController()

    variables: dict[str, str] = {"name": name}
    if post_id is not None:
        variables["post_id"] = post_id
    if network:
        variables["network"] = network

    def _render(template: str) -> str:
        try:
            return Template(template).render(**variables)
        except Exception:
            return template

    for entry in commands:
        if not entry:
            continue
        cmd = entry[0]
        args = entry[1:]
        if cmd == "open" and args:
            url = _render(args[0])
            _slow_print(f"Opening {url}")
            controller.open(url)
        elif cmd == "click" and args:
            selector = _render(args[0])
            _slow_print(f"Clicking {selector}")
            controller.click(selector)
        elif cmd == "fill" and len(args) == 2:
            selector, text = args
            selector = _render(selector)
            text = _render(text)
            _slow_print(f"Filling {selector}")
            controller.fill(selector, text)
        elif cmd == "run_js" and args:
            code = _render(args[0])
            _slow_print("Running JavaScript")
            controller.run_js(code)
        elif cmd == "run_js_file" and args:
            path = Path(args[0])
            if path.exists():
                _slow_print(f"Running JavaScript from {path}")
                controller.run_js(path.read_text())
            else:
                logger.error("JS file not found: %s", path)
        elif cmd == "run_applescript_file" and args:
            path = Path(args[0])
            if path.exists():
                _slow_print(f"Running AppleScript from {path}")
                proc = subprocess.run(
                    ["osascript", str(path)], capture_output=True, text=True
                )
                if proc.returncode != 0:
                    logger.error(proc.stderr.strip())
                elif proc.stdout:
                    logger.info(proc.stdout.strip())
            else:
                logger.error("AppleScript file not found: %s", path)
        elif cmd == "close_tab":
            _slow_print("Closing tab")
            controller.close_tab()
        elif cmd == "llm_query" and len(args) >= 2:
            response = args[1]
            store_as = args[2] if len(args) > 2 else None
            _slow_print(f"LLM response: {response}")
            if store_as:
                variables[store_as] = response
        elif cmd == "fetch_dom" and args:
            src_path = Path(args[0])
            dest = fixtures_root / name / src_path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dom = fetch_dom_html()
            dest.write_text(dom)
            _slow_print(f"Saved DOM to {dest}")
        elif cmd == "load_post" and len(args) >= 2:
            post_id = _render(args[0])
            network = _render(args[1])
            with SessionLocal() as session:
                preview = session.get(
                    PostPreview, {"post_id": post_id, "network": network}
                )
                post = session.get(Post, post_id)
            if preview and post:
                raw = preview.content
                m = re.search(r"```(?:json)?\s*(.*?)```", raw, flags=re.DOTALL)
                if m:
                    inner = m.group(1)
                    try:
                        data = json.loads(inner)
                    except json.JSONDecodeError as e:
                        logger.error("JSON parse error: %s", e)
                        data = None
                else:
                    logger.warning("No code-block found; using raw string")
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        data = None
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, str):
                            variables[key] = Template(value).render(post=post)
                    loaded = ", ".join(data.keys()) if data else ""
                    _slow_print(f"Preview loaded into variables: {loaded}")
                else:
                    variables["tweet"] = Template(raw).render(post=post)
                    _slow_print("Preview loaded into variables['tweet']")
            else:
                logger.error("Post or preview not found")
        elif cmd == "mark_published" and len(args) >= 2:
            post_id = _render(args[0])
            network = _render(args[1])
            tweet = variables.get("tweet")
            with SessionLocal() as session:
                if tweet is not None:
                    preview = session.get(
                        PostPreview, {"post_id": post_id, "network": network}
                    )
                    if preview is None:
                        preview = PostPreview(
                            post_id=post_id, network=network, content=tweet
                        )
                        session.add(preview)
                    else:
                        preview.content = tweet
                status = session.get(
                    PostStatus, {"post_id": post_id, "network": network}
                )
                if status is None:
                    status = PostStatus(
                        post_id=post_id, network=network, status="published"
                    )
                    session.add(status)
                else:
                    status.status = "published"
                session.commit()
            _slow_print(f"Marked {post_id} on {network} as published")
        else:
            logger.error("Unknown command: %s", cmd)
