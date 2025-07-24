# Preview Variables
Describe template variables loaded from post previews.

```json
{
  "title": "preview_variables",
  "description": "Variables extracted from PostPreview.content",
  "type": "object",
  "properties": {
    "tweet": {"type": "string", "description": "Main tweet text"},
    "img_url": {"type": "string", "description": "Optional image URL"},
    "tags": {"type": "string", "description": "Optional tag list"}
  }
}
```
