"""Showcase Jinja templating with the dspy LLM wrapper."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import select
import argparse

import dspy
from jinja2 import Template

from auto.db import SessionLocal
from auto.models import Post


from typing import Optional


def main(post_id: Optional[str] = None) -> None:
    """Render the preview template and send it to a local LLM."""
    template_path = os.getenv(
        "PREVIEW_TEMPLATE_PATH",
        Path(__file__).resolve().parents[1]
        / "auto"
        / "templates"
        / "medium_preview_prompt.txt",
    )

    if post_id is not None:
        stmt = select(Post).where(Post.id == post_id)
    else:
        stmt = (
            select(Post)
            .where(Post.content.is_not(None))
            .order_by(Post.created_at)
            .limit(1)
        )

    with SessionLocal() as session:
        post = session.execute(stmt).scalars().first()

    if post is None:
        print("No posts found")
        return

    message = Template(Path(template_path).read_text()).render(content=post.content)

    lm = dspy.LM("ollama_chat/gemma3:4b", api_base="http://localhost:11434", api_key="")
    dspy.configure(lm=lm)

    print(lm(messages=[{"role": "user", "content": message}]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize a Post with dspy")
    parser.add_argument(
        "--post-id",
        type=str,
        help="ID or URL of the Post to summarize",
    )
    args = parser.parse_args()
    main(post_id=args.post_id)
