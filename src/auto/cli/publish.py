"""Commands related to scheduling and previews."""

from __future__ import annotations

from typing import Optional
import json
from datetime import datetime, timezone

import typer
from sqlalchemy import select, case

from auto.cli.helpers import _parse_when, add_async_command
from auto.db import SessionLocal
from auto.models import Post, PostStatus, PostPreview, Task
from auto.preview import create_preview as _create_preview

app = typer.Typer(help="Publishing commands")
add_async_command(app)


@app.command()
def list_posts() -> None:
    """List stored posts with their ID and publish status."""

    exists_stmt = (
        select(PostStatus.post_id)
        .where(PostStatus.post_id == Post.id, PostStatus.status == "published")
        .exists()
    )

    stmt = select(
        Post.id,
        Post.title,
        case((exists_stmt, "published"), else_="pending").label("published"),
    ).order_by(Post.published.desc())

    with SessionLocal() as session:
        rows = session.execute(stmt).all()

    for post_id, title, published in rows:
        print(f"{post_id}\t{title}\t{published}")


@app.command("list-substacks")
def list_substacks(
    published: bool = typer.Option(
        False,
        "-p",
        "--published",
        help="Only show posts that have been shared",
    ),
    unpublished: bool = typer.Option(
        False,
        "-u",
        "--unpublished",
        help="Only show posts that have not been shared",
    ),
) -> None:
    """List posts, optionally filtering by publish status."""

    exists_stmt = (
        select(PostStatus.post_id)
        .where(PostStatus.post_id == Post.id, PostStatus.status == "published")
        .exists()
    )

    status_case = case((exists_stmt, "published"), else_="pending").label("published")

    stmt = select(Post.id, Post.title, status_case).order_by(Post.published.desc())

    if published and not unpublished:
        stmt = stmt.where(exists_stmt)
    elif unpublished and not published:
        stmt = stmt.where(~exists_stmt)

    with SessionLocal() as session:
        rows = session.execute(stmt).all()

    for post_id, title, status in rows:
        print(f"{post_id}\t{title}\t{status}")


@app.command()
def schedule(post_id: str, time: str, network: Optional[str] = None) -> None:
    """Schedule a post for publishing."""

    scheduled_at = _parse_when(time)
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
    else:
        scheduled_at = scheduled_at.astimezone(timezone.utc)
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
    print(
        f"Scheduled {post_id} for {', '.join(networks)} at {scheduled_at.isoformat()}"
    )


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


@app.command("list-schedule")
def list_schedule() -> None:
    """List scheduled posts with their network and timestamp."""

    stmt = select(
        PostStatus.post_id,
        PostStatus.network,
        PostStatus.scheduled_at,
        PostStatus.status,
    ).order_by(PostStatus.scheduled_at)

    with SessionLocal() as session:
        rows = session.execute(stmt).all()

    for post_id, network, scheduled_at, status in rows:
        when = scheduled_at.isoformat()
        print(f"{post_id}\t{network}\t{when}\t{status}")


@app.command()
def trending_tags(
    limit: int = 10, instance: Optional[str] = None, token: Optional[str] = None
) -> None:
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
def create_preview(
    post_id: str,
    network: str = "mastodon",
    when: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Schedule a preview generation task.

    If ``dry_run`` is true, print the scheduling info without
    writing to the database.
    """

    scheduled_at = _parse_when(when) if when else datetime.now(timezone.utc)

    with SessionLocal() as session:
        if session.get(Post, post_id) is None:
            print(f"Post {post_id} not found")
            return
        status = session.get(PostStatus, {"post_id": post_id, "network": network})
        if status is None:
            print(f"Post {post_id} is not scheduled for {network}")
            return
        payload = json.dumps({"post_id": post_id, "network": network})
        if dry_run:
            print(
                "Dry run: would schedule preview task for"
                f" {post_id} at {scheduled_at.isoformat()}"
            )
            return
        task = Task(type="create_preview", payload=payload, scheduled_at=scheduled_at)
        session.add(task)
        session.commit()
    print(f"Preview task scheduled for {post_id} at {scheduled_at.isoformat()}")


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

    with SessionLocal() as session:
        try:
            _create_preview(
                session,
                post_id,
                network,
                use_llm=use_llm,
                model=model,
                api_base=api_base,
                model_type=model_type,
            )
        except ValueError as exc:
            print(str(exc))
            return
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


@app.async_command()
async def sync_mastodon_posts() -> None:
    """Mark posts as published if they already appear on Mastodon."""
    from auto.db import SessionLocal
    from auto.models import Task
    from auto.mastodon_sync import handle_sync_mastodon_posts

    with SessionLocal() as session:
        task = Task(type="sync_mastodon_posts")
        await handle_sync_mastodon_posts(task, session)
