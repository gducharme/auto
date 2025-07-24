# Replay Variables
Provide template variables when replaying recorded commands.

```json
{
  "title": "replay_variables",
  "description": "Variables available to commands.json templates when invoking replay",
  "type": "object",
  "properties": {
    "name": {"type": "string", "description": "Fixture name under tests/fixtures"},
    "network": {"type": "string", "description": "Target social network"},
    "post_id": {"type": "string", "description": "Post ID or URL"}
  }
}
```
