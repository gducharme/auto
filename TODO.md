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
- ``load_dotenv`` is called in multiple modules (``db.py``, ``ingestion.py``, ``main.py``, ``mastodon_client.py``, ``tasks.py``). Centralize environment loading so configuration happens once.
- Several helpers fetch config values from ``os.getenv`` with defaults – e.g. ``get_feed_url``, ``get_database_url``, ``get_instance``, ``get_poll_interval``. Consider a unified configuration module.
- Tests repeatedly set up a temporary SQLite database with ``create_engine`` and ``init_db`` while monkeypatching ``auto.db.get_engine``. Provide a fixture to share this logic.
- ``DummyResponse`` classes for mocking ``requests.get`` appear in multiple test files. Factor them into a common helper.
- Many test modules modify ``sys.path`` to include the ``src`` directory. Consolidate this into ``conftest.py``.
