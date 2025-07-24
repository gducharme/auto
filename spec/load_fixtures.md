# Load Fixtures
Load schema and data from a SQL dump into the database.

```json
{
  "title": "load_fixtures",
  "description": "Load schema and data from a SQL file into the database",
  "type": "object",
  "properties": {
    "path": {"type": "string", "description": "SQL dump file to load"}
  }
}
```
