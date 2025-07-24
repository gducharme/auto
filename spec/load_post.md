# Load Post
Load preview content into variables for replay.

```json
{
  "title": "load_post",
  "description": "Load a post preview and store template variables",
  "type": "object",
  "properties": {
    "post_id": {"type": "string", "description": "ID of the post"},
    "network": {"type": "string", "description": "Target social network"}
  },
  "required": ["post_id", "network"]
}
```
