import pkg_resources
from pathlib import Path
import pytest


def _check_dependencies() -> None:
    requirements_file = Path(__file__).resolve().parents[1] / "requirements.txt"
    missing = []
    for line in requirements_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            pkg_resources.require(line)
        except Exception:
            missing.append(line)
    if missing:
        pytest.exit(
            "Missing dependencies: "
            + ", ".join(missing)
            + ".\nRun 'pip install -r requirements.txt' before running tests.",
            returncode=1,
        )


def pytest_configure(config):
    _check_dependencies()
