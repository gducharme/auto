from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from invoke import Exit

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


def _ci(ctx, upgrade: bool = False, freeze: bool = False) -> None:
    """Run the CI pipeline used by the ``ci`` Invoke task."""

    ctx.run("pip install -r requirements.txt", pty=True, echo=True)

    if upgrade:
        result = ctx.run("pip list --outdated --format=json", hide=True, warn=True)
        packages = [pkg["name"] for pkg in json.loads(result.stdout)]
        if packages:
            for pkg in packages:
                res = ctx.run(
                    f"pip install --upgrade {pkg}", warn=True, pty=True, echo=True
                )
                if res.exited != 0:
                    raise Exit(
                        "Dependency upgrade failed; manual intervention required",
                        code=res.exited,
                    )

    ctx.run("alembic upgrade head", pty=True, echo=True)
    ctx.run("pre-commit run --all-files", pty=True, echo=True)

    test_res = ctx.run("pytest --cov", warn=True, pty=True, echo=True)

    coverage = None
    for line in test_res.stdout.splitlines():
        if line.strip().startswith("TOTAL"):
            coverage = line.split()[-1]

    status = "passed" if test_res.ok else "failed"
    print(f"Tests {status}; coverage: {coverage or 'unknown'}")

    if upgrade and freeze:
        ctx.run("invoke freeze", pty=True, echo=True)
