Use the main db.py connection whenever possible
Use sqlalchemy models instead of sql statements when possible
Avoid reading environment variables at import time; retrieve them within functions so changes take effect without restarting.
Use context managers for database sessions instead of calling ``session.close()`` manually.
Configure logging in an explicit function and invoke it during application startup instead of at import time.
Encapsulate long-lived tasks or other state in classes rather than module-level globals to avoid race conditions.
