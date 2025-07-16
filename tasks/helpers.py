from __future__ import annotations

import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from auto.automation.safari import SafariController
from dateutil import parser


def _parse_when(value: str) -> datetime:
    """Parse relative or absolute time specifications."""
    value = value.strip().lower()
    m = re.match(r"(?:in\s+|\+)?(\d+)([smhd])$", value)
    if m:
        amount, unit = m.groups()
        delta = {
            "s": timedelta(seconds=int(amount)),
            "m": timedelta(minutes=int(amount)),
            "h": timedelta(hours=int(amount)),
            "d": timedelta(days=int(amount)),
        }[unit]
        return datetime.now(timezone.utc) + delta
    return parser.isoparse(value)


def _get_medium_magic_link() -> str | None:
    """Return the latest Medium magic link via Apple Mail if present."""
    script = Path(__file__).resolve().parents[1] / "scripts" / "fetch_medium_link.scpt"
    result = subprocess.run(["osascript", str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    match = re.search(r"https://medium\.com/(?:m/[^\s]+|magic/\S+)", result.stdout)
    return match.group(0) if match else None


def _fill_safari_tab(url: str, selector: str, text: str) -> str:
    """Open Safari to ``url`` and fill ``selector`` with ``text``."""
    controller = SafariController()
    controller.open(url)
    return controller.fill(selector, text)
