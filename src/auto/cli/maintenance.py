"""Server management and CI helpers."""

from __future__ import annotations

import subprocess

import typer

from auto.cli.helpers import freeze_requirements, update_dependencies, _ci

app = typer.Typer(help="Maintenance commands")


@app.command()
def ingest(host: str = "localhost", port: int = 8000) -> None:
    """Trigger the /ingest endpoint."""

    url = f"http://{host}:{port}/ingest"
    subprocess.run(["curl", "-s", "-X", "POST", url], check=True)


@app.command()
def uv(host: str = "127.0.0.1", port: int = 8000, reload: bool = True) -> None:
    """Start the FastAPI server using uvicorn."""

    reload_flag = "--reload" if reload else ""
    subprocess.run(
        ["uvicorn", "auto.main:app", reload_flag, "--host", host, "--port", str(port)],
        check=True,
    )


@app.command()
def freeze() -> None:
    """Regenerate requirements.txt without editable installs."""

    freeze_requirements()


@app.command()
def ci(upgrade: bool = False, freeze: bool = False) -> None:
    """Install dependencies, run migrations, lint and test."""

    _ci(upgrade=upgrade, freeze=freeze)


@app.command()
def update_deps(freeze: bool = False) -> None:
    """Upgrade dependencies to their latest versions."""

    update_dependencies(freeze=freeze)


@app.command()
def cleanup_branches(remote: str = "origin", main: str = "main") -> None:
    """Delete branches merged into ``main`` locally and on ``remote``."""
    from auto.git_utils import cleanup_merged_branches

    cleanup_merged_branches(remote=remote, main=main)


@app.command()
def metrics(host: str = "localhost", port: int = 8000) -> None:
    """Output Prometheus metrics from the running server."""

    url = f"http://{host}:{port}/metrics"
    subprocess.run(["curl", "-s", url], check=True)
