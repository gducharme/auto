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
    from sqlalchemy import select, exists, case
    from auto.db import SessionLocal
    from auto.models import Post, PostStatus

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


