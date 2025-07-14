# Auto

This project uses FastAPI with Alembic for database migrations.

## Running the server

Install dependencies and start the development server from the project root:

```bash
pip install -r requirements.txt
invoke uv
```

Running from the project root ensures Alembic can locate `alembic.ini` and migrations.
