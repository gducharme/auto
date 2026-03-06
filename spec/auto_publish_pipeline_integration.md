## Auto publish pipeline integration

Validate the end-to-end scheduling and auto-publish flow without making any
real network posts.

```json
{
  "title": "auto_publish_pipeline_integration",
  "description": "Schedule a post, let scheduler pick it up, and verify text passed to a fake social plugin",
  "inputs": {
    "post_id": {"type": "string", "description": "ID of the post to schedule"},
    "network": {"type": "string", "description": "Target network, e.g. mastodon"},
    "scheduled_at": {"type": "string", "description": "UTC timestamp or relative time expression"},
    "preview_content": {
      "type": "string",
      "description": "Optional templated preview message; fallback is '<title> <link>'"
    }
  },
  "assertions": [
    "publish.schedule creates/updates PostStatus and publish_post task",
    "process_pending executes publish_post task",
    "PostStatus transitions to published",
    "Task transitions to completed",
    "Text handed to plugin matches rendered preview or fallback"
  ]
}
```
