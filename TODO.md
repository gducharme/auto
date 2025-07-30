# TODO

## High Priority
- Replace all `print()` statements in CLI modules, `mastodon_sync.py`, and `preview.py` with logger calls so output respects the configured log level.


## Medium Priority
- Lazy‑load social network plugins via entry points instead of registering them on import in `socials/registry.py`.


## Low Priority
- Expand social network support beyond Mastodon.
- Containerize the application with a Dockerfile.
- ~~Add code coverage reporting for the test suite.~~

## Code Smells
- Unused imports reported by `ruff` should be cleaned up.
- AppleScript automation assumes the "Google" Mail account. Parameterize the account via an environment variable to support different setups.
- `mastodon_sync.py`, `preview.py` and the CLI modules print messages instead of using the logger.
- `socials/registry.py` registers plugins at import time causing side effects.
- Path lookups like `Path(__file__).resolve().parents[3]` break if the layout changes.

## DRY
- Factor out shared JSON parsing logic for LLM responses in `preview.py` and `automation/replay.py`.
- ~~Create a `PeriodicWorker` helper in `src/auto/utils/periodic.py` and use it in the scheduler and supervisor loops.~~
- Deduplicate synchronous wrappers like `fetch_feed()` and `post_to_mastodon()` by providing a common helper for running async code.
- Wrap CLI database access in a reusable session handler to remove repeated `SessionLocal()` blocks.
- Share a single logging setup between the main app and plan executor.

## BUGS

## RECS
- Allow configuring the Safari controller script path via a `SAFARI_SCRIPT` environment variable.
- Add a CLI wrapper for common tasks like listing posts or scheduling to reduce reliance on Invoke.
- Package the project so tests no longer modify `sys.path` directly.
- Provide invoke tasks `install_hooks`, `parse_plan`, and `setup` for routine development.
- Centralize configuration with a `Settings` class that loads environment variables at runtime.
