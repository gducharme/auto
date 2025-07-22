from importlib import metadata
from packaging.requirements import Requirement
from pathlib import Path
import sys
from sqlalchemy import create_engine
import pytest
import time

BASE_ROOT = Path(__file__).resolve().parents[1]
SRC = BASE_ROOT / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(BASE_ROOT))

from auto.utils import project_root  # noqa: E402
ROOT = project_root()

from auto.feeds.ingestion import init_db  # noqa: E402
from auto.db import SessionLocal  # noqa: E402


def _check_dependencies() -> None:
    requirements_file = ROOT / "requirements.txt"
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
    start = time.perf_counter()
    _check_dependencies()
    elapsed = time.perf_counter() - start
    print(f"dependency check: {elapsed:.2f}s")


@pytest.fixture
def test_db_engine(tmp_path, monkeypatch):
    """Return an initialized temporary SQLite engine for tests."""
    db_file = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_file}", connect_args={"check_same_thread": False}
    )
    t0 = time.perf_counter()
    init_db(str(db_file), engine=engine)
    elapsed = time.perf_counter() - t0
    print(f"DB setup took {elapsed:.3f}s")
    monkeypatch.setattr("auto.db.get_engine", lambda: engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(test_db_engine):
    """Provide an active SessionLocal bound to the test engine."""
    with SessionLocal() as session:
        yield session
