# Agent guidelines

These principles emphasize explicit initialization, safe resource handling, and minimal global state.

- UTC is life. Always use it, with timezones.
- Use the shared connection factory in `db.py` whenever possible.
- Prefer SQLAlchemy models rather than raw SQL statements.
- Retrieve environment variables inside functions so changes take effect without a restart.
- Manage database sessions with context managers instead of calling `session.close()` manually.
- Configure logging in a dedicated function invoked during startup, not at import time.
- Encapsulate long‑lived tasks or shared state in classes instead of module-level globals to avoid race conditions.
- When parsing feed entries, rely on the `_extract_text` helper in `feeds/ingestion.py` rather than branching on entry types.
- Avoid using Selenium for browser automation. Use the `SafariController`
  AppleScript from `automation/safari.py` instead.
- Typer doesn't support the ``str | None`` syntax. Use ``Optional[str]`` for
  command parameters.
- When implementing new features, also write the spec in the `spec` folder.

## Feature Design

Use Feature Design (FD) docs to scope, track, and close non-trivial work.

### Lifecycle

- Create new work as `FD-XXX` in `docs/features/`.
- Keep status current (`Open`, `In Progress`, `Blocked`, `Done`, `Deferred`).
- When complete or deferred, move the FD file to `docs/features/archive/` and update index tables.

### Required FD Skills

Use these Codex skills for FD workflow:

- `fd-new` to create a new FD item.
- `fd-explore` to gather repo and FD context.
- `fd-status` to review active FD state and index health.
- `fd-deep` for difficult design/implementation analysis.
- `fd-verify` for post-implementation verification readiness.
- `fd-close` to close/archive completed or deferred FD items.

### Conventions

- Keep one FD per discrete feature/change.
- Name files with stable `FD-XXX` prefixes.
- Include concrete verification steps in each FD.
- For this project, include related updates in `spec/` for implemented behavior.

### Index Management

- Keep `docs/features/FEATURE_INDEX.md` as the single source of truth for Active, Completed, Deferred/Closed, and Backlog items.
- Update the index whenever FD status changes.

### Commit Guidance

Repository history is mixed merge-commit plus concise imperative messages. For FD-specific commits, prefer:

- `FD-XXX: short description`

### Changelog

- Track notable user-facing changes in `CHANGELOG.md` under `## [Unreleased]`.
- Use Keep a Changelog sections (Added, Changed, Fixed, Removed, etc.) and release via semantic version tags.
- Python note: if you later want tag-driven version automation, consider `setuptools-scm>=8.0` with `pyproject.toml`.
