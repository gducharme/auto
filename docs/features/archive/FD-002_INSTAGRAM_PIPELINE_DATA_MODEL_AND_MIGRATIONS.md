# FD-002: Instagram Pipeline Data Model and Migrations

**Status:** Complete
**Completed:** 2026-03-06
**Priority:** High
**Effort:** Medium (1-4 hours)
**Impact:** Establishes persistent schema for concept generation, scoring, rendering, and publish pipeline state.

## Problem

The planned Instagram-native pipeline needs durable state for multiple concept candidates, score breakdowns, selected concept, render outputs, and publish attempt lifecycle. Current models (`Post`, `PostStatus`, `PostPreview`, `Task`) are insufficient for tracking multi-step creative workflows and retry-safe idempotency.

## Solution

Introduce dedicated schema and migration(s) for Instagram pipeline execution data:

1. Add pipeline run table keyed by `(post_id, network, pipeline_version)` with status, timestamps, and error context.
2. Add concept candidate table linked to run table with structured JSON payload and score fields.
3. Add selected concept/reference fields for deterministic downstream rendering.
4. Add render output table (asset refs, metadata, render status).
5. Add publish execution metadata to prevent duplicate publish and support retries.
6. Create Alembic migration(s) with backward-compatible defaults and UTC-safe timestamps.

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/auto/models.py` | MODIFY | Define new ORM models/relations for Instagram pipeline state. |
| `alembic/versions/*` | CREATE | Add migration(s) for new tables/indexes/constraints. |
| `src/auto/db.py` | MODIFY | Ensure model metadata remains migration-compatible. |
| `tests/*` | MODIFY | Add model/migration tests for schema correctness and constraints. |
| `spec/*` | CREATE/MODIFY | Add schema contract and migration verification notes. |

## Verification

1. Run migrations on empty DB and existing DB snapshot; both succeed.
2. Validate unique constraints prevent duplicate pipeline runs for same `(post_id, network, pipeline_version)`.
3. Validate foreign key integrity from concepts/render outputs to pipeline run.
4. Validate retry update path mutates existing run state without creating duplicate publish records.
5. Execute scheduler integration test using new schema with fake plugin and confirm publish idempotency behavior.

## Related

- `docs/features/FD-001_INSTAGRAM_NATIVE_AUTO_PUBLISH_PIPELINE.md`
- `spec/auto_publish_pipeline_integration.md`
