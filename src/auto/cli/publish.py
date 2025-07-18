"""Commands related to scheduling and previews."""

from __future__ import annotations

from typing import Optional

import typer
from sqlalchemy import select, case

from auto.cli.helpers import _parse_when
from auto.db import SessionLocal
from auto.models import Post, PostStatus, PostPreview

app = typer.Typer(help="Publishing commands")


@app.command()
def list_posts() -> None:
    """List stored posts with their ID and publish status."""

    exists_stmt = (
        select(PostStatus.post_id)
        .where(PostStatus.post_id == Post.id, PostStatus.status == "published")
        .exists()
    )

    stmt = (
        select(
            Post.id,
            Post.title,
            case((exists_stmt, "published"), else_="pending").label("published"),
        )
        .order_by(Post.published.desc())
    )

    with SessionLocal() as session:
        rows = session.execute(stmt).all()

    for post_id, title, published in rows:
        print(f"{post_id}\t{title}\t{published}")


@app.command()
def schedule(post_id: str, time: str, network: Optional[str] = None) -> None:
    """Schedule a post for publishing."""

    scheduled_at = _parse_when(time)
    networks = [network] if network else ["mastodon"]

    with SessionLocal() as session:
        if session.get(Post, post_id) is None:
            print(f"Post {post_id} not found")
            return
        for net in networks:
            ps = session.get(PostStatus, {"post_id": post_id, "network": net})
            if ps is None:
                ps = PostStatus(post_id=post_id, network=net, scheduled_at=scheduled_at)
                session.add(ps)
            else:
                ps.scheduled_at = scheduled_at
                ps.status = "pending"
            session.commit()
    print(f"Scheduled {post_id} for {', '.join(networks)} at {scheduled_at.isoformat()}")


@app.command()
def quick_post(network: str = "mastodon") -> None:
    """Schedule the oldest unshared post for publishing."""

    exists_stmt = (
        select(PostStatus.post_id)
        .where(
            PostStatus.post_id == Post.id,
            PostStatus.network == network,
            PostStatus.status == "published",
        )
        .exists()
    )

    stmt = select(Post).where(~exists_stmt).order_by(Post.created_at).limit(1)

    with SessionLocal() as session:
        post = session.execute(stmt).scalars().first()

    if not post:
        print("No unpublished posts found")
        return

    text = f"{post.title} {post.link}"
    print(text)

    if input("Publish? [y/N] ").strip().lower() != "y":
        print("Aborted")
        return

    schedule(post_id=post.id, time="in 1m", network=network)


@app.command()
def trending_tags(limit: int = 10, instance: Optional[str] = None, token: Optional[str] = None) -> None:
    """Display trending tags from Mastodon."""

    from mastodon import Mastodon
    from auto.config import get_mastodon_instance, get_mastodon_token

    instance = instance or get_mastodon_instance()
    token = token or get_mastodon_token()

    masto = Mastodon(access_token=token, api_base_url=instance)
    tags = masto.trending_tags(limit=limit)

    for tag in tags:
        name = tag["name"] if isinstance(tag, dict) else getattr(tag, "name", str(tag))
        print(name)


@app.command()
def list_previews() -> None:
    """List stored post previews."""

    from sqlalchemy import select

    stmt = select(PostPreview.post_id, PostPreview.network, PostPreview.content)
    with SessionLocal() as session:
        rows = session.execute(stmt).all()

    for post_id, network, content in rows:
        snippet = content.replace("\n", " ")[:60]
        print(f"{post_id}\t{network}\t{snippet}")


@app.command()
def generate_preview(
    post_id: str,
    network: str = "mastodon",
    use_llm: bool = False,
    model: str = "gemma-3-27b-it-qat",
    api_base: str = "http://localhost:1234/v1",
    model_type: str = "chat",
) -> None:
    """Generate or update a preview template for a scheduled post."""

    import dspy

    with SessionLocal() as session:
        status = session.get(PostStatus, {"post_id": post_id, "network": network})
        if status is None:
            print(f"Post {post_id} is not scheduled for {network}")
            return
        post = session.get(Post, post_id)
        if post is None:
            print(f"Post {post_id} not found")
            return
        preview = session.get(PostPreview, {"post_id": post_id, "network": network})

        if use_llm:
            try:
                lm = dspy.LM(model=model, api_base=api_base, api_key="", model_type=model_type)
                dspy.configure(lm=lm)
                prompt = (
                    f"Create a short template for sharing the post titled '{post.title}'. "
                    "Use { post.link } as a placeholder for the link."
                )
                content = dspy.chat(prompt).strip()
            except Exception as exc:
                print(f"LLM failed: {exc}; using default template")
                content = f"{post.title} {{ post.link }}"
        else:
            content = f"{post.title} {{ post.link }}"

        if preview is None:
            preview = PostPreview(post_id=post_id, network=network, content=content)
            session.add(preview)
        else:
            preview.content = content
        session.commit()
    print("Preview saved")


@app.command()
def edit_preview(post_id: str, network: str = "mastodon") -> None:
    """Interactively edit a post preview."""

    import click

    with SessionLocal() as session:
        preview = session.get(PostPreview, {"post_id": post_id, "network": network})
        existing = preview.content if preview else ""
        new = click.edit(existing)
        if new is None:
            print("No changes made")
            return
        new = new.rstrip("\n")
        if preview is None:
            preview = PostPreview(post_id=post_id, network=network, content=new)
            session.add(preview)
        else:
            preview.content = new
        session.commit()
    print("Preview updated")

