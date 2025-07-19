from __future__ import annotations

from invoke import task


@task
def install_deps(c):
    """Install project dependencies."""
    c.run("pip install -r requirements.txt", pty=True)


@task
def uv(c, host="127.0.0.1", port=8000, reload=True):
    """Start the FastAPI development server."""
    flag = "--reload" if reload else ""
    c.run(
        f"python -m auto.cli maintenance uv --host {host} --port {port} {flag}",
        pty=True,
    )


@task
def scheduler(c):
    """Run the background scheduler."""
    c.run("python -m auto.scheduler", pty=True)


@task
def ingest(c):
    """Manually trigger RSS ingestion."""
    c.run("python -m auto.cli maintenance ingest", pty=True)


@task
def list_previews(c):
    """List stored post previews."""
    c.run("python -m auto.cli publish list-previews", pty=True)


@task
def generate_preview(c, post_id, network="mastodon"):
    """Generate or update a preview for ``post_id``."""
    c.run(
        f"python -m auto.cli publish generate-preview --post-id {post_id} --network {network}",
        pty=True,
    )


@task
def edit_preview(c, post_id, network="mastodon"):
    """Interactively edit a stored preview."""
    c.run(
        f"python -m auto.cli publish edit-preview --post-id {post_id} --network {network}",
        pty=True,
    )


@task
def update_deps(c, freeze=False):
    """Upgrade dependencies to their latest versions."""
    flag = "--freeze" if freeze else ""
    c.run(f"python -m auto.cli maintenance update-deps {flag}", pty=True)


@task
def parse_plan(c):
    """Parse PLAN.md into task files."""
    c.run(
        "python -c 'from auto.plan.parser import parse_plan; parse_plan(\"PLAN.md\")'",
        pty=True,
    )


@task
def execute_plan(c, plan="plan.json"):
    """Run the automation plan executor."""
    c.run(f"python -m auto.automation.plan_executor {plan}", pty=True)


@task
def install_hooks(c):
    """Install pre-commit hooks."""
    c.run("pre-commit install", pty=True)


@task
def tests(c, marker=None):
    """Run the test suite."""
    cmd = "pytest"
    if marker:
        cmd += f" -m {marker}"
    c.run(cmd, pty=True)
