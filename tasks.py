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

