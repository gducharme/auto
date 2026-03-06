# FD-003: Instagram Intelligent Payload Adapter and Preview Surface

**Status:** Complete
**Completed:** 2026-03-06
**Priority:** High
**Effort:** High (> 4 hours)
**Impact:** Converts canonical pipeline payloads into Instagram-native publish-ready structures with deterministic adaptation and human-reviewable previews.

## Problem

Current pipeline output is useful but still generic. It does not yet provide a robust, format-aware conversion into Instagram-native publish structures (carousel/reel/single image) with explicit accessibility metadata, caption shaping, hashtag placement strategy, and clear operator preview before execution.

Without an adapter layer, payload quality and consistency depend on ad-hoc logic, making it difficult to maintain quality, enforce policy, and support future execution backends (API or Safari automation) reliably.

## Solution

Implement a dedicated adapter stage between planning and publish execution:

1. Add a versioned adapter contract that transforms canonical pipeline output into a strict Instagram publish schema.
2. Add format-specific adapter functions for carousel, reel, and single-image outputs.
3. Add deterministic caption/hashtag/CTA normalization rules and accessibility metadata generation.
4. Persist adapter output for observability and retry-safe execution.
5. Expand artifact export with rich preview assets to inspect the adapted payload before posting.
6. Add integration tests validating adapter outputs and execution handoff contract without real posting.

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/auto/instagram_adapter.py` | CREATE | Central adapter that maps canonical pipeline payload to Instagram-native schema. |
| `src/auto/instagram_pipeline.py` | MODIFY | Invoke adapter stage and persist/export adapter outputs. |
| `src/auto/models.py` | MODIFY | Add/adjust fields for adapter metadata/version if needed. |
| `alembic/versions/*` | MODIFY | Migrate schema changes required by adapter persistence. |
| `src/auto/scheduler.py` | MODIFY | Wire adapter-aware execution path and task payload handling. |
| `tests/test_instagram_pipeline_integration.py` | MODIFY | Validate adaptation + preview export + handoff behavior. |
| `tests/test_instagram_adapter.py` | CREATE | Unit tests for format-specific adaptation and normalization rules. |
| `spec/instagram_payload_adapter.md` | CREATE | Document adapter schema contract and verification matrix. |

## Verification

1. Unit tests cover deterministic adaptation for `carousel`, `reel`, and `single_image` concepts.
2. Adapter output includes required fields: `media_items`, `caption_final`, `alt_text`, `cta_strategy`, and `adapter_version`.
3. Integration test confirms pipeline run persists adapter payload and exports preview artifacts.
4. Integration test confirms handoff payload remains idempotent for `(post_id, network, pipeline_version)` run key.
5. No real network posting occurs in tests; fake plugin path only.

## Related

- `docs/features/FD-001_INSTAGRAM_NATIVE_AUTO_PUBLISH_PIPELINE.md`
- `docs/features/archive/FD-002_INSTAGRAM_PIPELINE_DATA_MODEL_AND_MIGRATIONS.md`
- `spec/instagram_pipeline_phase1.md`
