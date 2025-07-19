# TODO

## High Priority

- Remove the module-level scheduler globals and create `Scheduler` instances in `main.py`.

## Medium Priority
- Integrate the Medium automation client so posts can also be published there.
- Move plugin registration to `src/auto/socials/registry.py` and document how to write a plugin with an example `medium_client.py`.

## Low Priority
- Expand social network support beyond Mastodon.
- Containerize the application with a Dockerfile.
- ~~Add code coverage reporting for the test suite.~~

## Code Smells
- Unused imports reported by `ruff` should be cleaned up.
- AppleScript automation assumes the "Google" Mail account, which is brittle.

## DRY
- Create a `PeriodicWorker` helper in `src/auto/utils/periodic.py` and use it in the scheduler and supervisor loops.

## BUGS
- `schedule()` stores naive datetimes when no timezone is supplied, leading to
  inconsistent scheduling.

## RECS
- Add a CLI wrapper for common tasks like listing posts or scheduling to reduce reliance on Invoke.
- Package the project so tests no longer modify `sys.path` directly.
- Provide invoke tasks `install_hooks`, `parse_plan`, and `setup` for routine development.
- Centralize configuration with a `Settings` class that loads environment variables at runtime.
- Add a GitHub Actions workflow for tests, linting, and formatting.
