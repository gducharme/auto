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
    """Parse relative or absolute time specifications.

    Always return a timezone-aware UTC datetime.
    """
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

    dt = parser.isoparse(value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


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


def click_button_by_text(controller: SafariController, text: str) -> bool:
    """Click the first button containing ``text``.

    Returns ``True`` if the button was found and clicked.
    """
    quoted = json.dumps(text)
    find_btn_js = f"""
(() => {{
  const span = Array.from(document.querySelectorAll('button span.truncate'))
    .find(el => el.textContent.trim() === {quoted});
  return span ? span.closest('button').outerHTML : '';
}})()
"""
    btn_html = controller.run_js(find_btn_js)
    if not btn_html:
        return False

    click_btn_js = f"""
(() => {{
  const span = Array.from(document.querySelectorAll('button span.truncate'))
    .find(el => el.textContent.trim() === {quoted});
  if (span) {{
    span.closest('button').click();
    return 'clicked';
  }}
  return '';
}})()
"""
    return bool(controller.run_js(click_btn_js))


def update_dependencies(ctx, freeze: bool = False) -> None:
    """Upgrade outdated dependencies and optionally regenerate requirements."""

    res = ctx.run("pip list --outdated --format=json", hide=True, warn=True)
    packages = []
    if res.stdout.strip():
        try:
            packages = [pkg["name"] for pkg in json.loads(res.stdout)]
        except json.JSONDecodeError as exc:
            raise Exit(f"Failed to parse outdated packages: {exc}") from exc

    for pkg in packages:
        result = ctx.run(f"pip install --upgrade {pkg}", warn=True, pty=True, echo=True)
        if result.exited != 0:
            raise Exit(
                f"Failed to upgrade {pkg}; manual intervention required",
                code=result.exited,
            )

    check = ctx.run("pip check", warn=True, pty=True, echo=True)
    if check.exited != 0:
        raise Exit("Dependency conflicts remain after upgrade", code=check.exited)

    if freeze:
        ctx.run("invoke freeze", pty=True, echo=True)


def _ci(ctx, upgrade: bool = False, freeze: bool = False) -> None:
    """Run the CI pipeline used by the ``ci`` Invoke task."""

    ctx.run("pip install -r requirements.txt", pty=True, echo=True)

    if upgrade:
        update_dependencies(ctx, freeze=freeze)

    ctx.run("alembic upgrade head", pty=True, echo=True)
    ctx.run("pre-commit run --all-files", pty=True, echo=True)

    test_res = ctx.run("pytest --cov", warn=True, pty=True, echo=True)

    coverage = None
    for line in test_res.stdout.splitlines():
        if line.strip().startswith("TOTAL"):
            coverage = line.split()[-1]

    status = "passed" if test_res.ok else "failed"
    print(f"Tests {status}; coverage: {coverage or 'unknown'}")
