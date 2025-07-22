from __future__ import annotations


import dspy
from sqlalchemy.orm import Session

from .models import Post, PostStatus, PostPreview
from .socials.mastodon_client import fetch_trending_tags


def create_preview(
    session: Session,
    post_id: str,
    network: str = "mastodon",
    *,
    notes: str | None = None,
    tags_limit: int = 0,
    use_llm: bool = False,
    model: str = "gemma-3-27b-it-qat",
    api_base: str = "http://localhost:1234/v1",
    model_type: str = "chat",
) -> None:
    """Generate or update a preview for ``post_id`` and ``network``."""

    status = session.get(PostStatus, {"post_id": post_id, "network": network})
    if status is None:
        raise ValueError(f"Post {post_id} is not scheduled for {network}")

    post = session.get(Post, post_id)
    if post is None:
        raise ValueError(f"Post {post_id} not found")

    preview = session.get(PostPreview, {"post_id": post_id, "network": network})

    extra = ""
    if tags_limit > 0:
        tags = fetch_trending_tags(limit=tags_limit)
        if tags:
            extra += "\n" + " ".join(f"#{t}" for t in tags)
    if notes:
        extra += f"\n{notes}"

    if use_llm:
        try:
            lm = dspy.LM(
                model=model, api_base=api_base, api_key="", model_type=model_type
            )
            dspy.configure(lm=lm)
            prompt = (
                f"Create a short template for sharing the post titled '{post.title}'. "
                "Use { post.link } as a placeholder for the link." + extra
            )
            content = lm(messages=[{"role": "user", "content": prompt}]).strip()
        except Exception:
            content = f"{post.title} {{ post.link }}" + extra
    else:
        content = f"{post.title} {{ post.link }}" + extra

    if preview is None:
        preview = PostPreview(post_id=post_id, network=network, content=content)
        session.add(preview)
    else:
        preview.content = content

    session.commit()
