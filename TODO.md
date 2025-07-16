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

## BUGS
- The ``/ingest`` endpoint always returns success even if ``run_ingest`` fails
  to fetch or parse the feed, hiding ingestion errors from the caller.
  【F:src/auto/main.py†L27-L39】

## RECS
- Add a CLI wrapper for common tasks like listing posts or scheduling to reduce reliance on Invoke.
- Standardize timezone handling with aware datetime objects throughout the app.
- Consider asynchronous HTTP clients for feed ingestion and posting to improve throughput.
- Package the project so tests no longer modify `sys.path` directly.
