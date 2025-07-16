# TODO

## High Priority

- Move all environment variable access in ``feeds/ingestion.py`` and
  ``socials/mastodon_client.py`` into helper functions so new values are picked
  up without restarting.
- Reuse ``db.get_engine()`` from ``db.py`` instead of creating new engines in
  the ingestion helpers.

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
