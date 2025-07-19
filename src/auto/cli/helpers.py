from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time

from auto.automation.safari import SafariController
from dateutil import parser


def _delay(seconds: float) -> None:
    """Sleep for ``seconds`` or ``TASKS_DELAY`` env override."""
    override = os.getenv("TASKS_DELAY")
    try:
        wait = float(override) if override is not None else seconds
    except ValueError:
        wait = seconds
    time.sleep(wait)


def _slow_print(message: str) -> None:
    """Print ``message`` then pause for a short delay."""
    print(message)
    _delay(5)


def freeze_requirements() -> None:
    """Regenerate requirements.txt without editable installs."""
    res = subprocess.run(
        ["pip", "freeze", "--exclude-editable"], capture_output=True, text=True, check=True
    )
    Path("requirements.txt").write_text(res.stdout)


def _parse_when(value: str) -> datetime:
    """Parse relative or absolute time specifications.

    Always return a timezone-aware UTC datetime.
    """
    value = value.strip()
    m = re.match(r"(?:in\s+|\+)?(\d+)([smhd])$", value.lower())
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
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


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


def update_dependencies(freeze: bool = False) -> None:
    """Upgrade outdated dependencies and optionally regenerate requirements."""

    res = subprocess.run(
        ["pip", "list", "--outdated", "--format=json"],
        capture_output=True,
        text=True,
    )
    packages = []
    if res.stdout.strip():
        try:
            packages = [pkg["name"] for pkg in json.loads(res.stdout)]
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Failed to parse outdated packages: {exc}") from exc

    for pkg in packages:
        result = subprocess.run(["pip", "install", "--upgrade", pkg])
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to upgrade {pkg}; manual intervention required"
            )

    check = subprocess.run(["pip", "check"])
    if check.returncode != 0:
        raise RuntimeError("Dependency conflicts remain after upgrade")

    if freeze:
        freeze_requirements()


def _ci(upgrade: bool = False, freeze: bool = False) -> None:
    """Run the CI pipeline used by the ``ci`` command."""

    subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)

    if upgrade:
        update_dependencies(freeze=freeze)

    subprocess.run(["alembic", "upgrade", "head"], check=True)
    subprocess.run(["pre-commit", "run", "--all-files"], check=True)

    cmd = [
        "pytest",
        "--cov=src/auto",
        "--cov-report=term",
        "--cov-report=xml",
    ]
    if os.getenv("COVERAGE_HTML"):
        cmd.append("--cov-report=html")

    result = subprocess.run(cmd, text=True, capture_output=True)

    coverage = None
    for line in result.stdout.splitlines():
        if line.strip().startswith("TOTAL"):
            coverage = line.split()[-1]

    status = "passed" if result.returncode == 0 else "failed"
    print(f"Tests {status}; coverage: {coverage or 'unknown'}")
