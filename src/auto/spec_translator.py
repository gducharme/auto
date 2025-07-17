"""Translate Rotex specs into OpenAI-style function definitions."""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from jsonschema import Draft7Validator, exceptions


SCHEMA_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _sanitize_name(title: str) -> str:
    """Return a lowercase identifier derived from ``title``."""
    name = re.sub(r"\W+", "_", title.lower()).strip("_")
    return name or "function"


def translate(spec_text: str) -> Dict[str, Any]:
    """Parse a Rotex spec and return an OpenAI function definition.

    Parameters
    ----------
    spec_text:
        The Rotex specification text containing a JSON Schema block.

    Returns
    -------
    dict
        Mapping with ``name``, ``description`` and ``parameters`` keys.

    Raises
    ------
    ValueError
        If the spec does not contain a valid JSON Schema block.
    """

    if not isinstance(spec_text, str):
        raise TypeError("spec_text must be a string")

    m = SCHEMA_RE.search(spec_text)
    if not m:
        raise ValueError("JSON schema block not found")

    try:
        schema = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON schema: {exc}") from exc

    try:
        Draft7Validator.check_schema(schema)
    except exceptions.SchemaError as exc:
        raise ValueError(f"Schema validation failed: {exc}") from exc

    # title is the first Markdown heading
    title = ""
    description_lines = []
    for line in spec_text.splitlines():
        if line.startswith("#") and not title:
            title = line.lstrip("# ").strip()
            continue
        if line.strip().startswith("```json"):
            break
        if title:
            description_lines.append(line.strip())
    description = " ".join(l for l in description_lines if l).strip()

    name = _sanitize_name(title or schema.get("title", "function"))
    if not description:
        description = schema.get("description", "")

    return {"name": name, "description": description, "parameters": schema}
