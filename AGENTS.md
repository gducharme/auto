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
