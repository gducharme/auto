Context

This file captures the domain language, objectives, and guiding principles for our automated, self‑evolving content‑publishing platform. It is intended for the coding bot and human collaborators to align on the project’s purpose and terminology.

Project Objective

Automate the end‑to‑end distribution of Substack posts across multiple social platforms.

Continuously learn and adapt posting strategies based on engagement metrics.

Self‑heal broken connectors via vision‑driven fallbacks (MCP) when APIs or UIs change.

Balance automation with human‑in‑the‑loop checkpoints for setup, QA, and error recovery.

Domain Language & Key Concepts

Term

Meaning

Ingestion

Polling and parsing Substack RSS feeds into a normalized database of posts.

Normalization

Cleaning HTML, extracting excerpts, generating hashtags, resizing images.

Distribution

Pushing posts to social platforms (Mastodon, Twitter/X, Medium, etc.) with plugins.

Plugin

A module implementing post() and fetch_metrics() for one platform.

post_status

Table recording each post × network status, attempts, errors, timestamps, metrics.

Planner

Component that assigns variants (time slots, hooks) and schedules posts accordingly.

Experiment Engine

Runs A/B tests on variants, updates Planner configuration based on statistical results.

Metrics Harvester

Periodic jobs that retrieve engagement data and compute composite scores.

Human‑in‑Loop

Breakpoints where the system pauses and notifies an operator for manual intervention.

MCP

Vision‑based automation (Airtest, Lackey) to locate UI elements when code connectors fail.

Self‑Heal

Automatic detection of repeated failures and fallback to MCP scripts, with auto‑PRs.

Architectural Layers

Plan & Task Management: Parses the roadmap (PLAN.md) into discrete tasks, tracks status and manual checkpoints.

Code Generation & Testing: LLM‑driven code synthesis from function specs, unit tests, migrations, and static analysis.

Orchestration: Scheduler/queue (Celery or Cron+Invoke) driving ingestion, distribution, and metric collection workflows.

Distribution Plugins: Standalone modules for each platform, with both API and MCP fallback capabilities.

Analytics & Experimentation: Data pipelines that ingest engagement metrics, run significance tests, and feed results back to the Planner.

Monitoring & Notifications: Detect errors, manual tasks, and QA gates; notify operators via Slack/email; resume on approval.

Guiding Principles

Modularity: Keep each platform connector, analysis routine, and planner component independently testable.

Observability: Every step writes to logs and the database; metrics and errors must be traceable to source tasks.

Automation‑First: Default to code‑driven connectors and experiments; only pause for human action when truly needed.

Resilience: Use vision‑driven MCP fallbacks to survive UI/API changes without full rewrites.

Data‑Driven: Let engagement scores and statistical tests drive decisions about posting times, hooks, and variants.
