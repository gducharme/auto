import subprocess
from pathlib import Path


class SafariController:
    """Control Safari using AppleScript commands."""

    def __init__(self, script: Path | None = None) -> None:
        if script is None:
            script = (
                Path(__file__).resolve().parents[3] / "scripts" / "safari_control.scpt"
            )
        self.script = script

    def _run(self, command: str, *args: str) -> str:
        result = subprocess.run(
            ["osascript", str(self.script), command, *args],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        return result.stdout.strip()

    def open(self, url: str) -> str:
        """Open ``url`` in Safari, activating an existing tab if present."""
        return self._run("open", url)

    def click(self, selector: str) -> str:
        """Click the element matching ``selector``."""
        return self._run("click", selector)

    def fill(self, selector: str, text: str) -> str:
        """Fill ``selector`` with ``text``."""
        return self._run("fill", selector, text)

    def run_js(self, code: str) -> str:
        """Execute JavaScript ``code`` in the current tab."""
        return self._run("run_js", code)

    def close_tab(self) -> str:
        """Close the current Safari tab."""
        return self._run("close_tab")
