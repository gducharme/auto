"""Showcase Jinja templating with the dspy LLM wrapper."""

from __future__ import annotations

import os
from pathlib import Path

import dspy
from jinja2 import Template


def main() -> None:
    """Render the preview template and send it to a local LLM."""
    template_path = os.getenv(
        "PREVIEW_TEMPLATE_PATH",
        Path(__file__).resolve().parents[1]
        / "auto"
        / "templates"
        / "preview_prompt.txt",
    )

    content = "This is a demonstration post used to showcase the preview template."
    message = Template(Path(template_path).read_text()).render(content=content)

    lm = dspy.LM("ollama_chat/gemma3:4b", api_base="http://localhost:11434", api_key="")
    dspy.configure(lm=lm)

    print(lm(messages=[{"role": "user", "content": message}]))


if __name__ == "__main__":
    main()
