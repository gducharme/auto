from __future__ import annotations

import os
import json
import re
import logging
from pathlib import Path

import dspy
from jinja2 import Template
from sqlalchemy.orm import Session

from .models import Post, PostStatus, PostPreview

logger = logging.getLogger(__name__)


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
            raw = str(response).strip()

            m = re.search(r"```(?:json)?\s*(.*?)```", raw, flags=re.DOTALL)
            if m:
                inner = m.group(1)
                try:
                    data = json.loads(inner)
                except json.JSONDecodeError as e:
                    logger.debug("JSON parse error: %s", e)
                    data = None
            else:
                logger.debug("No code-block found; using raw string")
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = None

            if not isinstance(data, dict):
                data = {"tweet": raw}
        except Exception:
            logger.debug("LLM preview generation failed", exc_info=True)
            data = {"tweet": post.summary or post.title}
    else:
        data = {"tweet": post.summary or post.title}

    preview = session.get(PostPreview, {"post_id": post_id, "network": network})
    if preview is not None:
        session.delete(preview)

    preview = PostPreview(
        post_id=post_id,
        network=network,
        content=json.dumps(data),
    )
    session.add(preview)
    session.commit()
    logger.debug(json.dumps(data))
