# tasks.py
from invoke import task


@task
def ingest(ctx, host="localhost", port=8000):
    """
    Trigger the /ingest endpoint.
    Usage: invoke ingest --host 127.0.0.1 --port 8000
    """
    url = f"http://{host}:{port}/ingest"
    ctx.run(f"curl -s -X POST {url}", echo=True)


@task
def uv(ctx, host="127.0.0.1", port=8000, reload=True):
    """Start the FastAPI server using uvicorn."""
    reload_flag = "--reload" if reload else ""
    ctx.run(
        f"uvicorn auto.main:app {reload_flag} --host {host} --port {port}",
        pty=True,
        echo=True,
    )


@task
def freeze(ctx):
    """
    Regenerate requirements.txt without editable installs.
    Usage: invoke freeze
    """
    ctx.run("pip freeze --exclude-editable > requirements.txt", echo=True)


@task
def list_posts(ctx):
    """List stored posts with their ID and publish status."""
    from sqlalchemy import select, case
    from auto.db import SessionLocal
    from auto.models import Post, PostStatus

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


@task
def schedule(ctx, post_id, time, network=None):
    """Schedule a post for publishing.

    ``time`` may be an absolute ISO timestamp or a relative string like
    ``"in 1h"`` or ``"+30m"``. If ``--network`` is omitted the post is
    scheduled for all known networks.
    """
    import re
    from datetime import datetime, timedelta, timezone
    from dateutil import parser
    from auto.db import SessionLocal
    from auto.models import PostStatus

    def _parse_when(value: str) -> datetime:
        value = value.strip().lower()
        m = re.match(r"(?:in\s+|\+)?(\d+)([smhd])$", value)
        if m:
            amount, unit = m.groups()
            delta = {
                "s": timedelta(seconds=int(amount)),
                "m": timedelta(minutes=int(amount)),
                "h": timedelta(hours=int(amount)),
                "d": timedelta(days=int(amount)),
            }[unit]
            return datetime.now(timezone.utc) + delta
        return parser.isoparse(value)

    scheduled_at = _parse_when(time)
    if scheduled_at.tzinfo is not None:
        scheduled_at = scheduled_at.astimezone(timezone.utc).replace(tzinfo=None)
    networks = [network] if network else ["mastodon"]

    with SessionLocal() as session:
        for net in networks:
            ps = session.get(PostStatus, {"post_id": post_id, "network": net})
            if ps is None:
                ps = PostStatus(
                    post_id=post_id,
                    network=net,
                    scheduled_at=scheduled_at,
                )
                session.add(ps)
            else:
                ps.scheduled_at = scheduled_at
                ps.status = "pending"
            session.commit()
    print(
        f"Scheduled {post_id} for {', '.join(networks)} at {scheduled_at.isoformat()}"
    )


@task
def quick_post(ctx, network="mastodon"):
    """Schedule the oldest unshared post for publishing."""
    from sqlalchemy import select
    from auto.db import SessionLocal
    from auto.models import Post, PostStatus

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

    schedule(ctx, post_id=post.id, time="in 1m", network=network)


@task
def trending_tags(ctx, limit=10, instance=None, token=None):
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


@task
def chat(
    ctx,
    message=None,
    model="gemma-3-27b-it-qat",
    api_base="http://localhost:1234/v1",
    model_type="chat",
):
    """Send a chat message to a local LLM via dspy."""
    import dspy

    lm = dspy.LM(
        model=model,
        api_base=api_base,
        api_key="",
        model_type=model_type,
    )
    dspy.configure(lm=lm)

    default_question = "What is the typical silica (SiO₂) content in standard soda-lime glass, and how is it manufactured?"
    prompt = message or default_question
    response = dspy.chat(prompt)
    print(response)


def _get_medium_magic_link():
    """Return the latest Medium magic link via Apple Mail if present."""
    import subprocess
    import re
    from pathlib import Path

    script = Path(__file__).resolve().parent / "scripts" / "fetch_medium_link.scpt"
    result = subprocess.run(["osascript", str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    match = re.search(r"https://medium\.com/(?:m/[^\s]+|magic/\S+)", result.stdout)
    return match.group(0) if match else None


@task
def medium_magic_link(ctx):
    """Check Apple Mail once for a Medium magic link and print the result."""

    link = _get_medium_magic_link()
    if link:
        print(f"Found magic link: {link}")
    else:
        print("Magic link not found")


def _fill_safari_tab(url: str, selector: str, text: str) -> str:
    """Open Safari to ``url`` and fill ``selector`` with ``text``.

    Returns the JavaScript status string from the AppleScript.
    """
    import subprocess
    from pathlib import Path

    script = Path(__file__).resolve().parent / "scripts" / "safari_fill.scpt"
    result = subprocess.run(
        ["osascript", str(script), url, selector, text],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


@task
def safari_fill(ctx, url, selector, text):
    """Open or activate a Safari tab and type text into the given field."""
    result = _fill_safari_tab(url, selector, text)
    if result:
        print(result)


@task
def list_previews(ctx):
    """List stored post previews."""
    from sqlalchemy import select
    from auto.db import SessionLocal
    from auto.models import PostPreview

    stmt = select(PostPreview.post_id, PostPreview.network, PostPreview.content)
    with SessionLocal() as session:
        rows = session.execute(stmt).all()

    for post_id, network, content in rows:
        snippet = content.replace("\n", " ")[:60]
        print(f"{post_id}\t{network}\t{snippet}")


@task
def generate_preview(
    ctx,
    post_id,
    network="mastodon",
    use_llm=False,
    model="gemma-3-27b-it-qat",
    api_base="http://localhost:1234/v1",
    model_type="chat",
):
    """Generate or update a preview template for a scheduled post."""
    from auto.db import SessionLocal
    from auto.models import Post, PostStatus, PostPreview
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
                lm = dspy.LM(
                    model=model, api_base=api_base, api_key="", model_type=model_type
                )
                dspy.configure(lm=lm)
                prompt = (
                    f"Create a short template for sharing the post titled '{post.title}'. "
                    "Use {{ post.link }} as a placeholder for the link."
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


@task
def edit_preview(ctx, post_id, network="mastodon"):
    """Interactively edit a post preview."""
    import click
    from auto.db import SessionLocal
    from auto.models import PostPreview

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
