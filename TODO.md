# TODO

## High Priority

## Medium Priority
- Implement periodic/scheduled ingestion instead of manual triggering.
- Expose Prometheus metrics for published and failed posts to aid health
  monitoring.

## Low Priority
- Expand social network support beyond Mastodon.
- Containerize the application with a Dockerfile.
- Add integration tests covering ``MediumClient`` browser automation.

## Code Smells
- Config values like POLL_INTERVAL and POST_DELAY are set at import time and do not pick up environment changes.

## DRY
- Several helpers fetch config values from ``os.getenv`` with defaults – e.g. ``get_feed_url``, ``get_database_url``, ``get_instance``, ``get_poll_interval``. Consider a unified configuration module.
- Tests repeatedly set up a temporary SQLite database with ``create_engine`` and ``init_db`` while monkeypatching ``auto.db.get_engine``. Provide a fixture to share this logic.
- ``DummyResponse`` classes for mocking ``requests.get`` appear in multiple test files. Factor them into a common helper.
- Many test modules modify ``sys.path`` to include the ``src`` directory. Consolidate this into ``conftest.py``.

## BUGS
- ``updated_at`` columns on ``Post``, ``PostStatus`` and ``PostPreview`` are never refreshed when the rows are modified because they only use ``server_default`` and no ``onupdate`` callback.  Timestamps therefore become stale when statuses or previews change. 【F:src/auto/models.py†L13-L45】
- ``schedule`` allows timezone‑aware datetimes for relative values, but the
  scheduler compares naive UTC timestamps.  Persisting aware values may silently
  drop timezone information and lead to inconsistent schedules.
  【F:tasks.py†L75-L87】【F:src/auto/scheduler.py†L71-L74】
- ``schedule`` does not verify that the post ID exists before inserting a
  ``PostStatus`` record.  An invalid ID triggers a database integrity error
  instead of a clear message. 【F:tasks.py†L92-L105】
- The ``/ingest`` endpoint always returns success even if ``run_ingest`` fails
  to fetch or parse the feed, hiding ingestion errors from the caller.
  【F:src/auto/main.py†L27-L39】
