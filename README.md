# Auto

Auto is a small proof-of-concept for automatically reposting Substack articles
to other platforms.  It periodically ingests a Substack RSS feed and stores the
entries in a local SQLite database.  Those stored posts can then be published to
supported social networks – currently Mastodon – using small helper scripts.

The API itself is implemented with **FastAPI** and database migrations are
handled via **Alembic**.  The project is intentionally tiny but demonstrates the
basics needed for a multi‑publish workflow.

## Running the server

Install dependencies and start the development server from the project root:

```bash
pip install -r requirements.txt
invoke uv
```

Running from the project root ensures Alembic can locate `alembic.ini` and
migrations.

## Ingesting Substack posts

Once the server is running you can trigger an ingestion job:

```bash
invoke ingest
```

This fetches the configured Substack RSS feed and saves any new posts into the
database.

## Posting to social networks

The `src/auto/socials` directory contains simple clients for publishing to
different platforms.  For example `mastodon_client.py` posts a status to a
Mastodon instance.  Additional networks can be added in a similar way.  Each
post’s publish status per network is tracked in the `post_status` table.

While minimal, the goal is to provide the scaffolding for mirroring your
Substack content across multiple social sites with a single workflow.
