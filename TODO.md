# TODO

## High Priority

## Medium Priority
- Set up linting to run automatically on pre-commit.
- Implement periodic/scheduled ingestion instead of manual triggering.

## Low Priority
- Expand social network support beyond Mastodon.
- Containerize the application with a Dockerfile.

## Code Smells
- Config values like POLL_INTERVAL and POST_DELAY are set at import time and do not pick up environment changes.
