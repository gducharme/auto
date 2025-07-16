# Project Plan

This document outlines the phased roadmap for building the automated content pipeline. Each phase builds on the previous one and includes clear deliverables.

## Stand up CI/Dev environment

- Create the repository scaffold with `src/auto`, Alembic migrations, `tasks.py`, `.env` and `pre-commit`.
- Install the testing framework (**pytest**) and code-quality hooks.

## Agent integration

- Integrate the AI agent into the development loop via an editor extension or CLI wrapper so that it:
  1. Reads Rotex specs.
  2. Generates code files or pull requests.
  3. Runs tests and reports results.

## Phase 1 — Core Pipeline MVP (1–2 weeks)

Goal: get one platform working end to end under AI-generated supervision.

Rotex specs:
1. Poll & parse Substack RSS.
2. Normalize entries and generate excerpts.
3. Post to Mastodon.
4. Log results to the `post_status` table.

Deliverables:
- A runnable script (cron or `invoke ingest`) that ingests the feed, normalizes posts, publishes to Mastodon and logs results.
- Unit tests covering each module.
- Baseline metrics from the first five posts (replies, boosts, favourites).

## Phase 2 — Metric Collection & Scoring (1 week)

Goal: layer on metrics fetching and composite scoring.

Rotex specs:
5. Fetch engagement via the Mastodon API.
6. Compute `engagement_score` with configurable weights.
7. Persist scores back to the database.

Deliverables:
- Nightly job that retrieves engagement data and fills `metrics_*` fields.
- Dashboard or notebook showing baseline scores for the first five posts.
- Tests that simulate API responses and check the scoring logic.

## Phase 3 — Lean Experiment Engine (2 weeks)

Goal: automate A/B testing on a single variable and feed winners back into the dispatcher.

Rotex specs:
8. Define variants and assign them (e.g. time slot or hook style).
9. Analysis job that compares average scores per variant using a statistical test.
10. Planner that updates dispatcher config to use the winning variant.

Deliverables:
- New `variant` column in `post_status`.
- Automated variant assignment during ingest.
- Daily analysis report and automatic config adjustment.
- Tests that mock variant data and validate the analysis logic.

## Phase 4 — Modular Plugins & Multi-Platform (3 weeks)

Goal: abstract platform logic into plugins and add a second network.

Rotex specs:
11. Define a plugin interface with `post()` and `fetch_metrics()` methods.
12. Implement a Twitter/X plugin.
13. Refactor the dispatcher to iterate over enabled plugins.
14. Add a health-check job that pings each plugin.

Deliverables:
- `plugins/` folder with Mastodon and X modules.
- Dispatcher that fans out to both platforms.
- Health-check alerts sent to Slack or email.
- Integration tests using mocks for each plugin.

## Phase 5 — Self-Healing & Vision-Driven Fallback (4 weeks)

Goal: detect broken connectors and automatically generate fallback code.

Rotex specs:
15. Error detector that flags repeated failures.
16. Vision-based MCP script template (e.g. Lackey or Airtest).
17. Agent prompt design that reads error logs, infers new selectors or templates and generates updated plugin code.
18. CI pipeline step that runs MCP flows nightly against a staging page.

Deliverables:
- Automated fallback pipeline that switches to browser-based MCP mode on API failure.
- AI-generated pull requests for selector updates, validated by tests.
- Dashboard of connector uptime and auto-healing actions.

## Phase 6 — Continuous Meta-Automation (ongoing)

Goal: let the system propose new experiments and refactorings.

Rotex specs:
19. Generator that scans analytics and suggests new hypotheses (e.g. "Test 3-tag vs 5-tag sets on X").
20. Agent to scaffold new Rotex specs and submit pull requests for review.
21. Code-refactor alerts (e.g. duplicated code in plugins).

Deliverables:
- A "lab notebook" CLI where generated specs can be approved or refined.
- Periodic pull requests that expand test coverage or clean up code.
- A living system that, with minimal human guidance, writes new code to pursue higher engagement.

## Parallel activities

- Governance & review: weekly sprint check-ins to review AI-generated pull requests and metrics.
- Data-driven calibration: quarterly weight recalibration for the engagement formula.
- User feedback: early beta testers providing qualitative feedback to refine normalization, tone and variant dimensions.
