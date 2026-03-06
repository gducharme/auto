## Instagram pipeline phase 1

Deterministic Instagram-native planning, scoring, and gated publish simulation.

```json
{
  "title": "instagram_pipeline_phase1",
  "task_type": "instagram_pipeline_run",
  "task_payload": {
    "post_id": "string",
    "network": "instagram",
    "pipeline_version": "string",
    "auto_publish": "boolean"
  },
  "environment_gates": {
    "INSTAGRAM_PIPELINE_ENABLED": "1|0",
    "INSTAGRAM_PIPELINE_AUTO_PUBLISH": "1|0",
    "INSTAGRAM_PIPELINE_QUALITY_THRESHOLD": "float",
    "INSTAGRAM_PIPELINE_BANNED_TERMS": "comma-separated tokens",
    "INSTAGRAM_PIPELINE_EXPORT_ENABLED": "1|0",
    "INSTAGRAM_PIPELINE_EXPORT_DIR": "directory path for run artifacts"
  },
  "state_contract": {
    "run_statuses": ["pending", "ready", "needs_review", "disabled", "published"],
    "concept_count": "3 deterministic concepts per run",
    "selection": "highest score_total, rank 1",
    "publish_guard": "idempotent by (post_id, network, pipeline_version)"
  },
  "assertions": [
    "A run row is created or reused for the unique run key",
    "Concept rows are persisted with deterministic scores and rank",
    "Below-threshold or policy-blocked payloads are marked needs_review",
    "Disabled pipeline marks run disabled and does not publish",
    "Auto-publish uses plugin.post exactly once for same run key",
    "Successful publish updates PostStatus(post_id, network)=published",
    "Artifacts are exported to disk with run JSON, ranked concepts, payload, and preview files"
  ]
}
```
