"""Top-level CLI application."""

from __future__ import annotations

import typer
from importlib import import_module
from .helpers import add_async_command
from auto import configure_logging


def build_app() -> typer.Typer:
    app = typer.Typer()
    add_async_command(app)
    app.add_typer(import_module("auto.cli.publish").app, name="publish")
    app.add_typer(import_module("auto.cli.automation").app, name="automation")
    app.add_typer(import_module("auto.cli.maintenance").app, name="maintenance")
    return app


def __getattr__(name: str):
    if name in {"publish", "automation", "maintenance"}:
        return import_module(f"auto.cli.{name}")
    raise AttributeError(name)


def main() -> None:
    """Run the CLI application."""

    configure_logging()
    build_app()()


if __name__ == "__main__":  # pragma: no cover
    main()
