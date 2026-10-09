---
name: quay-n8n-boundaries
description: Decide what belongs in n8n vs. the QUAY app. Defines the orchestration boundary, idempotency rules, retry semantics, and the contract between n8n workflows and Supabase / Slack / the app.
---

# QUAY n8n Integration Boundaries

## Purpose

n8n is QUAY's orchestration glue across Slack, Drive, Read.ai, Monday, Supabase, and AI. Without a clear boundary, business logic ends up duplicated in nodes and routes, and the system becomes impossible to reason about. This skill defines what n8n does, what the app does, and how they communicate.

## When to use

- Designing any cross-system flow (Slack → Supabase → AI → Slack).
- Deciding whether new logic should be a workflow, an app route, or a Supabase function.
- Reviewing an existing workflow that has grown into a mini-application.
- Wiring a new event source through n8n into the activity feed.

Do **not** use it for in-app interactions that don't cross a system boundary — those stay in the app.

## Expected inputs

1. **Trigger** — what kicks off the work (webhook, schedule, Supabase row, Slack event).
2. **Systems involved** — every external system the flow touches.
3. **Data writes** — what Supabase rows are created/updated, by which credential.
4. **Failure cost** — what happens if a step partially completes.
5. **SLA** — when this needs to finish (seconds, minutes, eventually).

## The boundary

**n8n owns:**

- Cross-system orchestration: anything that reads or writes more than one external system.
- Scheduled jobs that aren't tied to a user request.
- Long-running or retried steps (anything > 10s wall clock).
- Fan-out workflows (one trigger → many sub-actions).
- Webhook ingestion from Slack, Read.ai, Drive, Monday.

**The app (Next.js routes, server actions, edge functions) owns:**

- Synchronous user requests with a short SLA (< 2s).
- All authorization checks — n8n trusts the app's RLS, never re-implements it.
- Anything that requires user session context.
- Anything reading member-visible data.

**Supabase owns:**

- Data storage, RLS, and minimal triggers (just `updated_at` and referential housekeeping).
- It does **not** initiate workflows; it emits events that n8n listens to.

**The AI layer ([quay-ai-feature-implementation](../ai-feature-implementation/SKILL.md)) owns:**

- All model calls, prompt versioning, and tool definitions.
- Called *from* n8n or the app, never directly from Supabase triggers or Slack handlers.

## Contract between n8n and the rest

- **Schemas at every boundary.** Every webhook into n8n and every callback from n8n is validated against a Zod/JSON schema kept in `schemas/`.
- **Idempotency is mandatory.** Every workflow accepts and respects an `idempotency_key`. Re-running with the same key produces zero side effects.
- **One credential per integration.** n8n holds the Supabase service-role key, Slack bot token, and AI keys — the *app* does not proxy them.
- **Workflows write to Supabase via dedicated, narrow RPCs.** No raw SQL from n8n; named functions only, so the surface area is reviewable.
- **All meaningful steps emit an `activity_event`** (see [quay-activity-feed-model](../activity-feed-model/SKILL.md)).

## Constraints

- A workflow that crosses three or more systems must have a written failure-handling note (what's retryable, what's dead-letter).
- No workflow runs a model call inline with a Slack response that the user is waiting on; use an async pattern with an "I'll get back to you" reply.
- No workflow writes to Supabase with a service-role key while bypassing the RPC layer.
- No secrets in workflow JSON exports committed to git — use n8n credential references.

## Anti-patterns

- A Slack slash command that calls n8n which calls the app which calls n8n again. Pick a direction and keep it acyclic.
- Two workflows that do the same thing slightly differently — one is wrong; merge them.
- "Just put it in a Code node" — if a Code node is more than 30 lines, it belongs in the app, not in n8n.
- Workflows that depend on the order of arrays in webhook payloads — payloads are unordered.
- A workflow that triggers itself on its own writes — silent infinite loops.

## Checklist

- [ ] Trigger, systems, writes, failure cost, SLA listed.
- [ ] Decision documented: why n8n (cross-system orchestration) vs. app (synchronous, authz, member-visible).
- [ ] Every webhook in/out validated against a schema.
- [ ] Idempotency key handling defined.
- [ ] Supabase writes go through named RPCs, not raw SQL.
- [ ] At least one `activity_event` is emitted per workflow.
- [ ] Failure handling note: retryable steps + dead-letter target.
- [ ] No Code node > 30 lines.
- [ ] No service-role key or token in the workflow JSON.

## Example prompt

> A new requirement: when Read.ai posts a transcript webhook, summarize it with Claude, write the summary + a `mentor.session_completed` event to Supabase, and post a one-line note in the cohort Slack channel. Decide what belongs in n8n vs. the app per `skills/quay/n8n-boundaries/SKILL.md`. Output the boundary decision, schemas needed, idempotency rule, and the failure-handling note. Do not implement.
