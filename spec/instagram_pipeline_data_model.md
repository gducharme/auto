## Instagram pipeline data model

Schema contract for storing Instagram-native planning, scoring, render outputs,
and publish lifecycle state.

```json
{
  "title": "instagram_pipeline_data_model",
  "description": "Persistent schema for Instagram-native pipeline runs, concepts, and assets",
  "tables": [
    {
      "name": "instagram_pipeline_runs",
      "keys": ["id"],
      "uniques": [["post_id", "network", "pipeline_version"]],
      "purpose": "Top-level run record and idempotency boundary"
    },
    {
      "name": "instagram_pipeline_concepts",
      "keys": ["id"],
      "uniques": [["run_id", "concept_key"]],
      "purpose": "Candidate concepts and score payloads"
    },
    {
      "name": "instagram_pipeline_assets",
      "keys": ["id"],
      "uniques": [["run_id", "asset_key"]],
      "purpose": "Rendered asset references and render status"
    }
  ],
  "verification": [
    "Migration creates all three tables on fresh DB",
    "Run uniqueness prevents duplicate (post_id, network, pipeline_version)",
    "Concept and asset rows can be inserted and linked to run records"
  ]
}
```
