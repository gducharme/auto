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
