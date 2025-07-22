import json
from pathlib import Path
from typing import Mapping, Any
from jinja2 import Template


def load_commands(
    name: str,
    *,
    variables: Mapping[str, Any] | None = None,
    root: Path | None = None,
) -> list[list[str]]:
    """Return commands for ``name`` rendered with ``variables``."""

    if root is None:
        root = Path(__file__).resolve().parents[3] / "tests" / "fixtures"
    path = root / name / "commands.json"
    data: list[list[str]] = json.loads(path.read_text())
    if not variables:
        return data

    rendered: list[list[str]] = []
    for entry in data:
        rendered_entry: list[str] = []
        for val in entry:
            if isinstance(val, str):
                rendered_entry.append(Template(val).render(**variables))
            else:
                rendered_entry.append(val)
        rendered.append(rendered_entry)
    return rendered
