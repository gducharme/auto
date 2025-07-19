"""Top-level CLI application."""

from __future__ import annotations

import typer
from .helpers import add_async_command

from . import publish, automation, maintenance

app = typer.Typer()
add_async_command(app)
app.add_typer(publish.app, name="publish")
app.add_typer(automation.app, name="automation")
app.add_typer(maintenance.app, name="maintenance")


def main() -> None:
    """Run the CLI application."""

    app()


if __name__ == "__main__":  # pragma: no cover
    main()
