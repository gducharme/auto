## Instagram payload adapter

Defines canonical-to-Instagram conversion contract used by the Instagram pipeline.

```json
{
  "title": "instagram_payload_adapter",
  "adapter_version": "ig-adapter-v1",
  "input_contract": {
    "post_id": "string",
    "network": "instagram",
    "format": "carousel|reel|single_image",
    "hook": "string",
    "caption_seed": "string",
    "hashtags": ["string"],
    "alt_text": "string",
    "cta_strategy": "string",
    "asset_plan": {
      "visual_rhythm": ["string"],
      "source_link": "string",
      "source_title": "string"
    }
  },
  "output_contract": {
    "adapter_version": "string",
    "publish_format": "carousel|reel|single_image",
    "media_items": [
      {
        "position": "number",
        "media_type": "image|video",
        "intent": "string",
        "uri": "string|null"
      }
    ],
    "caption_final": "string",
    "first_comment_hashtags": "string",
    "hashtags": ["normalized hashtags"],
    "accessibility": {
      "alt_text_primary": "string",
      "alt_text_by_media": [{"index": "number", "alt_text": "string"}]
    }
  },
  "assertions": [
    "Hashtags are normalized, deduplicated, and bounded",
    "Format-specific media_items contract is deterministic",
    "caption_final always exists",
    "Backward compatibility fields are still populated for publish path"
  ]
}
```
