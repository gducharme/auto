Use the main db.py connection whenever possible
Use sqlalchemy models instead of sql statements when possible
Avoid reading environment variables at import time; retrieve them within functions so changes take effect without restarting.
