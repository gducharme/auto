from __future__ import annotations

import os
from pathlib import Path

import dspy
from jinja2 import Template
from sqlalchemy.orm import Session

from .models import Post, PostStatus, PostPreview


def create_preview(
    session: Session,
    post_id: str,
    network: str = "mastodon",
    *,
    template_path: str | None = None,
    use_llm: bool = True,
) -> None:
    """Generate or update a preview for ``post_id`` and ``network``."""

    status = session.get(PostStatus, {"post_id": post_id, "network": network})
    if status is None:
        raise ValueError(f"Post {post_id} is not scheduled for {network}")

    post = session.get(Post, post_id)
    if post is None:
        raise ValueError(f"Post {post_id} not found")

    if template_path is None:
        template_path = os.getenv("PREVIEW_TEMPLATE_PATH")
    if template_path is None:
        template_path = (
            Path(__file__).resolve().parent
            / "templates"
            / f"{network}_preview_prompt.txt"
        )
    template_str = Path(template_path).read_text()
    message = Template(template_str).render(content=post.content or "", post_id=post_id)

    if use_llm:
        try:
            lm = dspy.LM(
                "ollama_chat/gemma3:12b",
                api_base="http://localhost:11434",
                api_key="",
            )
            dspy.configure(lm=lm)
            response = lm(messages=[{"role": "user", "content": message}])
            if isinstance(response, list):
                response = response[0]
            content = str(response).strip()
        except Exception:
            content = post.summary or post.title
    else:
        content = post.summary or post.title

    preview = session.get(PostPreview, {"post_id": post_id, "network": network})
    if preview is not None:
        session.delete(preview)

    preview = PostPreview(post_id=post_id, network=network, content=content)
    session.add(preview)
    session.commit()
    print(content)
