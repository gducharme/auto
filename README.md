# Auto

![Auto Logo](docs/logo.png)

Auto is a small proof-of-concept for automatically reposting Substack articles
to other platforms.  It periodically ingests a Substack RSS feed and stores the
entries in a local SQLite database.  Those stored posts can then be published to
supported social networks – currently Mastodon – using small helper scripts.

The API itself is implemented with **FastAPI** and database migrations are
handled via **Alembic**.  The project is intentionally tiny but demonstrates the
basics needed for a multi‑publish workflow.

## Quick Start

Clone the repository and install its dependencies:

```bash
git clone <repo-url>
cd auto
pip install -r requirements.txt
```

Copy the provided environment template and start the server and scheduler:

```bash
cp .env.sample .env
python -m auto.cli maintenance uv        # run the FastAPI server
python -m auto.scheduler                 # run the background scheduler
```

For development details see [CONTRIBUTING.md](CONTRIBUTING.md).

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
- `INGEST_INTERVAL` – seconds between automatic feed ingestions,
  default `600`.
- `POST_DELAY` – pause after each publish attempt, default `1` second.
- `MASTODON_SYNC_DEBUG` – set to `1` to print Mastodon statuses during sync.
- `SKIP_SLOW_PRINT` – set to `1` to disable delays in CLI output.
- `LOG_LEVEL` – log verbosity used by `configure_logging()`, default `INFO`.

Log output is sent to stdout when `configure_logging()` is called at
startup.  Adjust `LOG_LEVEL` to control the amount of detail.

## Running the server

Install dependencies (which include **lxml** for XML parsing) and start the development server from the project root:

```bash
pip install -r requirements.txt
python -m auto.cli maintenance uv
```

Running from the project root ensures Alembic can locate `alembic.ini` and
migrations.

## Scheduler

The background scheduler is started automatically during application
startup.  The FastAPI lifespan in `src/auto/main.py` creates a
`Scheduler` instance and calls its `start()` method, which continuously
executes entries from the `tasks` table.  Tasks have a ``type`` and
optional JSON payload.  Current
types are ``publish_post`` and ``ingest_feed``.  You can also run the
scheduler on its own:

```bash
python -m auto.scheduler
```
The command logs when the loop starts and stops so you know it's running.

## Ingesting Substack posts

The application automatically ingests the configured RSS feed on a
schedule controlled by `INGEST_INTERVAL`. Ingestion runs are stored as
``ingest_feed`` tasks so the scheduler can trigger them. You can also
trigger a run manually:

```bash
python -m auto.cli maintenance ingest
```

Both methods fetch the configured RSS feed and store any new posts in the
database.

## Posting to social networks

The `src/auto/socials` directory contains simple clients for publishing to
different platforms.  For example `mastodon_client.py` posts a status to a
Mastodon instance.  Additional networks can be added in a similar way.  Each
post’s publish status per network is tracked in the `post_status` table.

While minimal, the goal is to provide the scaffolding for mirroring your
Substack content across multiple social sites with a single workflow.

### Scheduling posts

Posts are queued with the `python -m auto.cli publish schedule` command. The time argument accepts
absolute ISO timestamps or relative values like `"+30m"`. Timestamps without a
timezone are interpreted in UTC and stored as timezone-aware datetimes.
Run `python -m auto.cli publish list-schedule` to see all upcoming posts and their networks.

### Listing Substack posts

View stored posts from the RSS feed with:

```bash
python -m auto.cli publish list-substacks
```

Use `-p` for only shared posts or `-u` for those not yet shared.

## Managing previews

Previews are small templates used when posting to other networks. They can be listed, generated or edited with CLI commands:

```bash
python -m auto.cli publish list-previews
python -m auto.cli publish generate-preview --post-id <id> --network mastodon
python -m auto.cli publish edit-preview --post-id <id> --network mastodon
python -m auto.cli publish delete-preview --post-id <id> --network mastodon
```

`generate-preview` uses a local LLM when available and falls back to a simple template. Previews are only created when the post has been scheduled.
The template can reference the original post URL via `{{ post_id }}`.

For a step-by-step walkthrough of generating, scheduling and editing previews, see [docs/previews.md](docs/previews.md).

## Syncing Mastodon posts

If you previously published to Mastodon outside of Auto, run the sync command to
mark matching posts as published:

```bash
python -m auto.cli publish sync-mastodon-posts
```

Set `MASTODON_SYNC_DEBUG=1` to print the fetched statuses while syncing.

### Viewing trending tags

Fetch the current trending tags from your Mastodon instance:

```bash
python -m auto.cli publish trending-tags --limit 10
```

Pass `--instance` and `--token` to override the defaults from the environment.

## Writing social network plugins

Plugins implement the `SocialPlugin` protocol defined in `src/auto/socials/base.py`. Create a module under `src/auto/socials/` and register an instance in `src/auto/socials/registry.py`. The plugin's `network` attribute is used to look it up when publishing. See [docs/plugins.md](docs/plugins.md) for a walkthrough and the `medium_client.py` example.


## Health checks

The scheduler checks for the presence of the `tasks` table when it
starts.  Ensure this table exists and watch the logs for any publishing
errors.  Production deployments should also expose metrics such as
Prometheus counters for successful and failed posts to provide better
visibility.

## Development

Install the pre-commit hooks so formatting and linting run automatically:

```bash
pre-commit install
```

The hooks mirror the CI checks, running `ruff check .`, `black --check .`, and
`pytest` on every commit to ensure consistent formatting, linting, and tests
continue to pass.

Use `python -m auto.cli maintenance update-deps` to upgrade outdated dependencies. Pass `--freeze` to
rewrite `requirements.txt` after the upgrades.

Convenient wrappers for these scripts are also available as Invoke tasks. Run `invoke --list` to see
the full set and pass `--help` to any task for usage details. For example:

```bash
invoke create-preview --help
```

## Plan parser

The project plan in `PLAN.md` can be turned into machine-readable task files.
`src/auto/plan/parser.py` extracts each bullet or numbered item and writes a
`.task` file per entry. These files live under `src/plan/`.

Regenerate them with:

```bash
python -c 'from auto.plan.parser import parse_plan; parse_plan("PLAN.md")'
```

## Plan executor

The step executor automates small browser tasks using the
[`SafariController`](src/auto/automation/safari.py). Our guidelines recommend
avoiding Selenium, so this controller is used instead. A plan is defined in
`plan.json`, but a working copy `plan_work.json` is updated after each step.
Generate a new plan automatically if the file does not exist and run it with:

```bash
python -m auto.automation.plan_executor plan.json
```

DOM snapshots and backups are written alongside the plan so failures can be
inspected or rolled back. Use the `--reset` flag to delete the working plan and
all generated artifacts.

Recorded browser sessions can be replayed with either the direct command or the
``invoke`` wrapper:

```bash
python -m auto.cli automation replay facebook --post-id 42 --network mastodon
# or simply
invoke replay facebook --post-id 42 --network mastodon
```

You can also queue a fixture for the scheduler to run later:

```bash
python -m auto.cli automation queue-replay facebook --post-id 42 --network mastodon
```

This creates a `replay_fixture` task that loads `tests/fixtures/facebook/commands.json` and executes it.

For ad-hoc experimentation you can launch an interactive Safari control menu:

```bash
python -m auto.cli automation control-safari
```

Alongside opening pages and clicking selectors, the menu now includes
"run_js_file", "run_applescript_file", and "llm_query" options to execute code
from external files or query a local LLM. Use "abort" to exit without saving a
test, or "quit" to write out the recorded steps. This makes it easy to inject
helper functions, run custom AppleScript snippets, or save responses from an LLM
prompt.

The ``llm_query`` option uses the same dspy configuration as the ``dspy_exp``
experiment script, connecting to an Ollama instance running locally.

## Running tests

Before running tests, install the project dependencies. The
`pytest-recording` plugin is included here and provides the
`--block-network` and `--record-mode` options configured in
`pytest.ini`:

```bash
pip install -r requirements.txt
```

Then run the unit test suite with `pytest`. Integration tests are skipped by
default because they require real credentials and network access. To run
them, set `MEDIUM_EMAIL` and `MEDIUM_PASSWORD` and pass the `integration`
marker:

```bash
pytest -m integration
```

### Network isolation

Tests are executed with [`pytest-recording`](https://pypi.org/project/pytest-recording/)
in `--block-network` mode. This prevents unexpected connections to the real
internet. Recorded HTTP interactions are stored as VCR cassettes under a
`cassettes/` directory next to each test module. To allow live recording or
network access, override the default options:

```bash
pytest --record-mode=new_episodes
```


## License

Distributed under the [MIT License](LICENSE).
