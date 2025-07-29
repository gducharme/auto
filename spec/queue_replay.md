# Queue Replay
Queue a replay_fixture task via the CLI.

```json
{
  "title": "queue_replay",
  "description": "Queue a replay_fixture task through the CLI",
  "type": "object",
  "properties": {
    "name": {"type": "string", "description": "Fixture name under tests/fixtures"},
    "post_id": {"type": "string", "description": "ID of the post"},
    "network": {"type": "string", "description": "Target social network"}
  },
  "required": ["name", "post_id", "network"]
}
```
