# Mark Published
Record that a post was successfully published on a network.
The interactive `mark_published` command uses stored `post_id` and `network`
variables to update both the `PostPreview` and `PostStatus` tables.

```json
{
  "title": "mark_published",
  "description": "Record that a post has been published on a network",
  "type": "object",
  "properties": {
    "network": {"type": "string", "description": "Social network name"},
    "post_id": {"type": "string", "description": "ID of the post"}
  },
  "required": ["network", "post_id"]
}
```
