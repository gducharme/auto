# TODO

## High Priority

## Medium Priority
- Expose Prometheus metrics for published and failed posts to aid health
  monitoring.

## Low Priority
- Expand social network support beyond Mastodon.
- Containerize the application with a Dockerfile.

## Code Smells

## DRY
- ``DummyResponse`` classes for mocking ``requests.get`` appear in multiple test files. Factor them into a common helper.

## BUGS
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

## RECS
- Add a CLI wrapper for common tasks like listing posts or scheduling to reduce reliance on Invoke.
- Standardize timezone handling with aware datetime objects throughout the app.
- Consider asynchronous HTTP clients for feed ingestion and posting to improve throughput.
- Package the project so tests no longer modify `sys.path` directly.

