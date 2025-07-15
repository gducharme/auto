# TODO

## High Priority

## Medium Priority
- Implement periodic/scheduled ingestion instead of manual triggering.
- Set up CI to run tests and linting automatically.

## Low Priority
- Expand social network support beyond Mastodon.
- Containerize the application with a Dockerfile.

## Code Smells
- Logging configuration occurs in __init__.py during import, which can interfere with embedding in other applications.
- scheduler.py stores global state in the `_task` variable which can lead to race conditions if start() is called multiple times.
- Parsing logic in feeds/ingestion.py has many branches and could be simplified or documented better.
- Config values like POLL_INTERVAL and POST_DELAY are set at import time and do not pick up environment changes.
