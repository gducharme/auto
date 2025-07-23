from __future__ import annotations

from invoke import task


@task
def install_deps(c):
    """Install project dependencies."""
    c.run("pip install -r requirements.txt", pty=True)


@task(
    help={
        "host": "Interface to bind the server to",
        "port": "Port number for the development server",
        "reload": "Reload on code changes",
    }
)
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


@task(
    help={
        "published": "Only show posts that have been shared",
        "unpublished": "Only show posts not yet shared",
    }
)
def list_substacks(c, published=False, unpublished=False):
    """List posts from the database."""
    pub_flag = "-p" if published else ""
    unpub_flag = "-u" if unpublished else ""
    c.run(
        f"python -m auto.cli publish list-substacks {pub_flag} {unpub_flag}",
        pty=True,
    )


@task
def list_schedule(c):
    """List scheduled posts across all networks."""
    c.run("python -m auto.cli publish list-schedule", pty=True)


@task(
    help={
        "post_id": "ID of the post to schedule",
        "when": "Publish time (e.g. '+10m' or ISO timestamp)",
        "network": "Target social network (default: mastodon)",
    }
)
def schedule(c, post_id, when, network="mastodon"):
    """Schedule a post for publishing."""
    c.run(
        f"python -m auto.cli publish schedule {post_id} {when} --network {network}",
        pty=True,
    )


@task(
    help={
        "post_id": "ID of the post to generate a preview for",
        "network": "Target social network (default: mastodon)",
    }
)
def generate_preview(c, post_id, network="mastodon"):
    """Generate or update a preview for ``post_id``."""
    c.run(
        f"python -m auto.cli publish generate-preview {post_id} --network {network}",
        pty=True,
    )


@task(
    help={
        "post_id": "ID of the post to generate a preview for",
        "network": "Target social network (default: mastodon)",
        "use_llm": "Generate the preview using the LLM",
    }
)
def create_preview(c, post_id, network="mastodon", use_llm=False):
    """Generate a preview template via the LLM."""
    cmd = f"python -m auto.cli publish create-preview {post_id} --network {network}"
    if use_llm:
        cmd += " --use-llm"
    c.run(cmd, pty=True)


@task(
    help={
        "post_id": "ID of the post to edit",
        "network": "Target social network (default: mastodon)",
    }
)
def edit_preview(c, post_id, network="mastodon"):
    """Interactively edit a stored preview."""
    c.run(
        f"python -m auto.cli publish edit-preview {post_id} --network {network}",
        pty=True,
    )


@task(
    help={
        "post_id": "ID of the post to delete",
        "network": "Target social network (default: mastodon)",
    }
)
def delete_preview(c, post_id, network="mastodon"):
    """Remove a stored preview."""
    c.run(
        f"python -m auto.cli publish delete-preview {post_id} --network {network}",
        pty=True,
    )


@task(
    help={
        "limit": "Number of tags to display",
        "instance": "Mastodon instance URL",
        "token": "Access token for the instance",
    }
)
def trending_tags(c, limit=10, instance=None, token=None):
    """Display trending tags from Mastodon."""
    cmd = f"python -m auto.cli publish trending-tags --limit {limit}"
    if instance:
        cmd += f" --instance {instance}"
    if token:
        cmd += f" --token {token}"
    c.run(cmd, pty=True)


@task
def sync_mastodon_posts(c):
    """Mark posts as published if they already appear on Mastodon."""
    c.run("python -m auto.cli publish sync-mastodon-posts", pty=True)


@task(help={"freeze": "Rewrite requirements.txt after upgrading"})
def update_deps(c, freeze=False):
    """Upgrade dependencies to their latest versions."""
    flag = "--freeze" if freeze else ""
    c.run(f"python -m auto.cli maintenance update-deps {flag}", pty=True)


@task(
    help={
        "remote": "Remote repository name",
        "main": "Name of the main branch",
    }
)
def cleanup_branches(c, remote="origin", main="main"):
    """Delete branches merged into main locally and on the remote."""
    c.run(
        f"python -m auto.cli maintenance cleanup-branches --remote {remote} --main {main}",
        pty=True,
    )


@task(
    help={
        "host": "Server host",
        "port": "Port serving metrics",
    }
)
def metrics(c, host="localhost", port=8000):
    """Output Prometheus metrics from the running server."""
    c.run(
        f"python -m auto.cli maintenance metrics --host {host} --port {port}",
        pty=True,
    )


@task
def safari_control(c):
    """Open the interactive Safari controller menu."""
    c.run("python -m auto.cli automation control-safari", pty=True)


@task(
    help={
        "name": "Fixture name under tests/fixtures",
        "network": "Target social network (default: mastodon)",
        "post_id": "Post ID for template variables",
    },
    positional=["name"],
)
def replay(c, name="facebook", network="mastodon", post_id=None):
    """Replay recorded Safari commands."""
    cmd = "python -m auto.cli automation replay"
    if name != "facebook":
        cmd += f" --name {name}"
    if network != "mastodon":
        cmd += f" --network {network}"
    if post_id:
        cmd += f" --post-id {post_id}"
    c.run(cmd, pty=True)


@task(help={"post_id": "ID or URL of the post to summarize"})
def dspy_exp(c, post_id):
    """Run the standalone dspy experiment."""

    c.run(
        f"python -m auto.cli automation dspy-experiment --post-id {post_id}",
        pty=True,
    )


@task
def parse_plan(c):
    """Parse PLAN.md into task files."""
    c.run(
        "python -c 'from auto.plan.parser import parse_plan; parse_plan(\"PLAN.md\")'",
        pty=True,
    )


@task(help={"plan": "Path to the plan JSON file"})
def execute_plan(c, plan="plan.json"):
    """Run the automation plan executor."""
    c.run(f"python -m auto.automation.plan_executor {plan}", pty=True)


@task
def install_hooks(c):
    """Install pre-commit hooks."""
    c.run("pre-commit install", pty=True)


@task(help={"marker": "Only run tests matching this marker"})
def tests(c, marker=None):
    """Run the test suite."""
    cmd = "pytest"
    if marker:
        cmd += f" -m {marker}"
    c.run(cmd, pty=True)


@task
def help(c):
    """List available invoke tasks."""
    c.run("invoke --list", pty=True)
