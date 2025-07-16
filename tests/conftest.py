from importlib import metadata
from packaging.requirements import Requirement
from pathlib import Path
import pytest


def _check_dependencies() -> None:
    requirements_file = Path(__file__).resolve().parents[1] / "requirements.txt"
    missing = []
    for line in requirements_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        req = Requirement(line)
        if req.marker and not req.marker.evaluate():
            continue
        try:
            installed = metadata.version(req.name)
        except metadata.PackageNotFoundError:
            missing.append(line)
        else:
            if req.specifier and installed not in req.specifier:
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
