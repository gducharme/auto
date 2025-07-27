# Replay Fixture Task
Schedule the replay of recorded automation commands.

```json
{
  "title": "replay_fixture",
  "description": "Run a recorded automation fixture via the scheduler",
  "type": "object",
  "properties": {
    "name": {"type": "string", "description": "Fixture name under tests/fixtures"},
    "post_id": {"type": "string", "description": "ID of the post"},
    "network": {"type": "string", "description": "Target social network"}
  },
  "required": ["name", "post_id", "network"]
}
```
