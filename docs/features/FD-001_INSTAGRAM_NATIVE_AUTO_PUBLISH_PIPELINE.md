# FD-001: Instagram Native Auto Publish Pipeline

**Status:** In Progress
**Priority:** High
**Effort:** High (> 4 hours)
**Impact:** Enables fully automated, Instagram-native creative generation and publishing with minimal/no manual artifact handling.

## Problem

Current social posting flow is largely cross-post oriented and not Instagram-native. It lacks a code-driven strategy for visual-first creative variants (carousel/reel/story style), concept scoring, and automated selection/publishing. The desired outcome is a zero- or near-zero-manual workflow that still optimizes for Instagram engagement patterns (hook, visual rhythm, save/share intent) rather than outbound-link-first behavior.

## Solution

Implement a dedicated Instagram-native pipeline task that:

1. Ingests source post content and generates multiple Instagram-native creative concepts.
2. Scores concepts programmatically (visual potential, engagement potential, effort/risk) and selects the best candidate.
3. Produces structured publish payloads (slide plan/reel plan, caption, hashtags, alt text, CTA strategy) without requiring standalone manual artifacts.
4. Renders publish-ready assets through deterministic templates/tooling.
5. Queues and executes posting through existing scheduler/replay automation paths, with configurable safety gates (auto-approve on/off, thresholds, policy checks).
6. Persists all intermediate/final data in DB-backed records for observability and retries.

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/auto/*` | MODIFY | Add Instagram-native planning, scoring, rendering, and task orchestration components. |
| `src/auto/scheduler.py` | MODIFY | Register and execute new Instagram pipeline task handlers. |
| `src/auto/cli/*` | MODIFY | Add commands to queue/run Instagram-native pipeline tasks. |
| `src/auto/models.py` (+ migration) | MODIFY | Persist concept candidates, selected plan, rendered assets, and pipeline state. |
| `tests/*` | MODIFY | Add unit/integration tests for scheduler pickup, concept selection, and non-network publish simulation. |
| `spec/*` | CREATE/MODIFY | Specify pipeline behavior, contracts, and verification scenarios. |

## Verification

### Test Matrix

| Layer | Scenario | Expected Result |
|------|----------|-----------------|
| Unit | Concept generator produces `N` candidates from a source post | Deterministic schema-valid concept list with required fields (hook, format, slides/reel plan, caption seed). |
| Unit | Concept scorer ranks candidates | Stable rank ordering for fixed seed/input; top concept has highest total weighted score. |
| Unit | Fallback behavior when concept generation/scoring fails | Pipeline falls back to safe default concept and does not crash scheduler loop. |
| Unit | Caption/hashtag/alt-text synthesis | Output respects configured bounds (length, hashtag count, banned term policy). |
| Unit | Render planner transforms concept to asset plan | Produces valid render instructions for carousel/reel templates. |
| Integration | `publish.schedule` + pipeline queue command creates due task(s) | Task rows are created with expected payloads and `pending` status. |
| Integration | `process_pending` picks up Instagram-native pipeline task | Task transitions `pending -> running -> completed` and persists outputs. |
| Integration | Pipeline with fake plugin (no network) auto-post path | Fake plugin receives final payload exactly once; `PostStatus` updated to `published`. |
| Integration | Retry path on transient plugin/render failure | Task status transitions to `error`, attempts increment, and next retry succeeds without duplicate publish. |
| Integration | Replay/automation bridge receives selected final message+asset refs | Replay command variables are rendered correctly and fixture commands execute without unknown-command errors. |
| E2E (opt-in) | AppleScript-enabled Safari path runs against saved HTML fixtures | JS helpers and posting command sequence execute end-to-end in supported macOS environments. |
| E2E (opt-in) | Dry-run full pipeline from post ingestion to ready-to-publish package | End state contains selected concept, render outputs, and queued publish action with no manual artifacts required. |

### Pass Criteria

1. All new unit/integration tests pass in CI default test suite (excluding opt-in AppleScript tests).
2. AppleScript-gated tests pass in optional macOS workflow when `RUN_APPLESCRIPT_TESTS=1`.
3. No real external posting occurs in automated tests; all posting verification uses fake/stub plugins.
4. Pipeline tasks are idempotent for retries (no duplicate publishes for same post/network/version).
5. Observability fields are persisted: selected concept ID, score breakdown, render status, publish status, error context.

### Rollout Gates

1. `Gate A - Planning only`: Generate + score concepts, persist selected plan, no rendering/publishing.
2. `Gate B - Render dry run`: Enable rendering pipeline with local artifacts/DB metadata only, still no posting.
3. `Gate C - Fake publish`: Route final payload to fake plugin in production-like scheduler path.
4. `Gate D - Controlled auto-publish`: Enable real publish for a narrow allowlist (single network/account) with kill switch.
5. `Gate E - Default on`: Expand scope once success/error-rate thresholds are met for consecutive runs.

### Operational Safeguards

- Global kill switch env flag to disable Instagram-native autopublish without redeploy.
- Minimum quality threshold for selected concept; below-threshold items are marked `needs_review` and not posted.
- Policy/banned-term guardrail before render and before publish.
- Duplicate-publish guard keyed by `(post_id, network, pipeline_version)`.

## Related

- `docs/features/FEATURE_INDEX.md`
- Existing replay fixture/scheduler pipeline work
- `spec/auto_publish_pipeline_integration.md`
- `spec/safari_js_integration.md`
