# Auto

Auto is a small proof-of-concept for automatically reposting Substack articles
to other platforms.  It periodically ingests a Substack RSS feed and stores the
entries in a local SQLite database.  Those stored posts can then be published to
supported social networks – currently Mastodon – using small helper scripts.

The API itself is implemented with **FastAPI** and database migrations are
handled via **Alembic**.  The project is intentionally tiny but demonstrates the
basics needed for a multi‑publish workflow.

## Environment variables

Copy `.env.sample` to `.env` and adjust the values or export them manually.
The following variables are used:

- `SUBSTACK_FEED_URL` – RSS feed to ingest posts from. Defaults to
  `https://geoffreyducharme.substack.com/feed` if unset.
- `DATABASE_URL` – database connection string (defaults to SQLite).
- `MASTODON_INSTANCE` – base URL of the Mastodon instance, default
  `https://mastodon.social`.
- `MASTODON_TOKEN` – access token for posting to Mastodon.
- `MEDIUM_EMAIL` – email address used to sign in to Medium.
- `MEDIUM_PASSWORD` – password for the Medium account.
- `MAX_ATTEMPTS` – maximum number of publish attempts before giving up.
- `SCHEDULER_POLL_INTERVAL` – seconds between scheduler iterations,
  default `5`.
- `POST_DELAY` – pause after each publish attempt, default `1` second.
- `LOG_LEVEL` – log verbosity used by `configure_logging()`, default `INFO`.

Log output is sent to stdout when `configure_logging()` is called at
startup.  Adjust `LOG_LEVEL` to control the amount of detail.

## Running the server

Install dependencies (which include **lxml** for XML parsing) and start the development server from the project root:

```bash
pip install -r requirements.txt
invoke uv
```

Running from the project root ensures Alembic can locate `alembic.ini` and
migrations.

## Scheduler

The background scheduler is started automatically during application
startup.  The FastAPI lifespan in `src/auto/main.py` calls
`scheduler.start()` which continuously invokes `process_pending` to
publish queued posts.  You can also run it on its own:

```bash
python -m auto.scheduler
```

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

## Managing previews

Previews are small templates used when posting to other networks. They can be listed, generated or edited with Invoke tasks:

```bash
invoke list-previews
invoke generate-preview --post-id <id> --network mastodon
invoke edit-preview --post-id <id> --network mastodon
```

`generate-preview` uses a local LLM when available and falls back to a simple template. Previews are only created when the post has been scheduled.


## Health checks

The scheduler checks for the presence of the `post_status` table when it
starts.  Ensure this table exists and watch the logs for any publishing
errors.  Production deployments should also expose metrics such as
Prometheus counters for successful and failed posts to provide better
visibility.

## Development

Install the pre-commit hooks so formatting and linting run automatically:

```bash
pre-commit install
```

## Running tests

Run the unit test suite with `pytest`. Integration tests are skipped by
default because they require real credentials and network access. To run
them, set `MEDIUM_EMAIL` and `MEDIUM_PASSWORD` and pass the `integration`
marker:

```bash
pytest -m integration
```

## License

Distributed under the [MIT License](LICENSE).
