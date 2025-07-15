# TODO

## High Priority

## Medium Priority
- Implement periodic/scheduled ingestion instead of manual triggering.
- Set up CI to run tests and linting automatically.

## Low Priority
- Expand social network support beyond Mastodon.
- Containerize the application with a Dockerfile.

## Code Smells
- Parsing logic in feeds/ingestion.py has many branches and could be simplified or documented better.
- Config values like POLL_INTERVAL and POST_DELAY are set at import time and do not pick up environment changes.
