# TODO

## High Priority

## Medium Priority
- Expose Prometheus metrics for published and failed posts to aid health
  monitoring.
 - Integrate the Medium automation client so posts can also be published there.

## Low Priority
- Expand social network support beyond Mastodon.
- Containerize the application with a Dockerfile.
- Add code coverage reporting for the test suite.

## Code Smells
- Unused imports reported by `ruff` should be cleaned up.
- AppleScript automation assumes the "Google" Mail account, which is brittle.

## DRY
- The scheduler classes share very similar start/stop loops.

## BUGS
- `schedule()` stores naive datetimes when no timezone is supplied, leading to
  inconsistent scheduling.

## RECS
- Add a CLI wrapper for common tasks like listing posts or scheduling to reduce reliance on Invoke.
- Package the project so tests no longer modify `sys.path` directly.
