---
name: quay-integration-contract-reviewer
description: Audits the contracts between QUAY surfaces — Slack bot, n8n, platform, Supabase, Drive, Read.ai, Sheets. Catches schema drift, producer/consumer mismatches, missing idempotency keys, hardcoded test secrets, undocumented versioning, and webhook-response inconsistencies.
---

# Purpose

The most expensive QUAY bugs come from contracts: a field name that means one thing on the producer side and another on the consumer side, a webhook that has a header today and doesn't tomorrow, an `emittedAt` that's UTC in one place and local in another. These bugs are silent (no error), late (manifests only with specific data), and hard to triage (involves multiple systems).

This skill enumerates every cross-system contract in QUAY, audits each against a contract spec, and emits findings for every gap.

# When to Use

- Every full audit; every `pre-deploy` audit if integration code was touched.
- Adding any new event source or sink.
- When a workflow misfires in a way that looks like a "data shape" issue.
- Before formalizing internal event contracts as a documented `N8N_EVENT_CONTRACTS`-style doc.

# Expected Inputs

1. The list of producer-consumer pairs in QUAY.
2. Any schema definitions (Zod, JSON Schema, TypeScript types, SQL DDL).
3. n8n workflow definitions showing payload shapes.
4. Slack event subscription configurations.
5. Read.ai webhook configuration.

# Required Context to Inspect

- `schemas/`, `types/`, `lib/types/` directories.
- n8n workflows that consume webhooks.
- Slack handler code.
- Supabase RPC signatures.
- `skills/quay/activity-feed-model/SKILL.md` (event shape).
- `skills/quay/n8n-boundaries/SKILL.md` (contract rules).

# Review Methodology

Enumerate every contract, then audit each.

## Enumerate

Common QUAY contracts:

| # | Producer | Consumer | Payload |
|---|---|---|---|
| 1 | Slack (event subscription) | n8n trigger | Slack event JSON |
| 2 | Read.ai | n8n trigger | Transcript / meeting webhook |
| 3 | Drive (watch) | n8n trigger | File change notification |
| 4 | n8n | Supabase RPC | Named parameter call |
| 5 | n8n | Slack chat.postMessage | Block kit JSON |
| 6 | Supabase | n8n (DB webhook or polling) | Row event |
| 7 | Internal portal | Supabase | Direct queries via JS client |
| 8 | Internal portal | n8n | Manual trigger webhooks |
| 9 | Slack bot (interactivity) | Internal API | Action payload |
| 10 | App | AI provider | Prompt payload |
| 11 | Activity event ingest | Activity feed table | Event row shape |
| 12 | Cron / scheduled | n8n | Self |

## Audit each contract against the contract spec

For each contract, verify:

| Concern | Pass criterion |
|---|---|
| Schema declared | A typed schema (Zod, JSON Schema, TS) defines the payload — not just an example. |
| Schema versioned | Schema has a `version` field; consumer rejects unknown versions explicitly. |
| Required fields | Each required field is named and validated. |
| Optional fields | Each optional field has a default behavior. |
| Field semantics | Field names are unambiguous (`createdAt` vs `emittedAt` vs `occurredAt` — pick one and use consistently). |
| Timestamps | UTC ISO-8601 with timezone. No "20240301" or "March 1." |
| IDs | Stable IDs (event ID, message ID) — usable as idempotency keys. |
| Headers | Required headers documented (signature, idempotency key, request ID, version). |
| Idempotency | Producer attaches a stable key; consumer respects it. |
| Versioning | Breaking changes go through versioned payloads; not silent. |
| Response shape | Webhook responses are defined (status code, body schema if any). |
| Error semantics | Producer knows which errors are retryable vs not, from response codes. |
| Examples | At least one happy-path and one error-path example. |
| Test fixtures | A consumer test loads a real producer payload sample. |

## Detect drift

- Producer schema vs consumer schema: do they match exactly?
- Same payload consumed in two places: do they parse it the same way?
- Schema changes in git history: were consumers updated in the same commit / PR?

# Severity System

- **P0** — Any of:
  - Producer-consumer mismatch in production that can silently corrupt data (producer adds a required field; consumer treats absence as a different thing).
  - A test-environment URL or secret is hardcoded in the production producer config.
  - Webhook with no signature verification (covered also in `adversarial-operations-reviewer`).
  - Idempotency key contract violated — producer sends one, consumer ignores; or producer doesn't send, consumer assumes one.
- **P1** — Schema is implicit (no formal type), so changes are unenforced. Timestamps inconsistent across producers. Required fields not validated. No versioning.
- **P2** — Field naming inconsistent (`user_id` vs `userId` vs `member_id`). Optional fields handled inconsistently. Headers undocumented.
- **P3** — Examples missing. Comments out of date.

# Checklist

- [ ] Contract inventory complete (one row per producer-consumer pair).
- [ ] Each contract has a typed schema in a known location (`schemas/`).
- [ ] Each contract has at least one example payload (happy + error).
- [ ] Each contract has a versioning policy.
- [ ] Each contract specifies headers (signature, idempotency key, version, request ID).
- [ ] Timestamps are ISO-8601 UTC across the board.
- [ ] Idempotency key contract is consistent: producer always sends or never; consumer respects.
- [ ] Webhook responses defined (status codes, body shape).
- [ ] No test URL / test webhook secret in production.
- [ ] When a schema changes, the PR shows both producer and consumer updated in lockstep (or behind a version flag).
- [ ] Schema changes are reflected in the activity-feed payload if relevant.

# QUAY-Specific Questions

- The **Slack event payload**: what events does the bot subscribe to? Are there events the bot processes that aren't in the subscription (impossible) or events subscribed but not handled (likely)?
- The **Read.ai webhook**: documented shape? Idempotent? Does it include a meeting ID, participant list, transcript URL, or inline transcript? If transcript inline, what's the size?
- The **Drive watch**: produces what payload? Is the file ID enough, or do we need full metadata?
- The **n8n → Supabase RPC**: each RPC has a SQL signature — is it stable? Has it been added to without versioning?
- The **Activity event** payload: shape declared in `quay-activity-feed-model`? Does every producer respect the shape?
- The **Slack → portal interactivity**: when a staff member clicks "approve" in a Slack block, what payload arrives at the portal? Is it verified?
- **Sheets ↔ Supabase sync** (if any): is there a defined shape for the rows, or does the n8n flow assume column order? Column-order assumptions are brittle.

# Common Failure Modes

- **The example-as-spec.** Documentation shows a payload example; no schema. The example was correct when written; the actual producer added a field three months ago; consumers vary in handling.
- **The "we just trust the payload" trap.** No validation; bad data eventually arrives; failures are confusing.
- **The header that's sometimes present.** `X-Request-ID` is sent by Slack but not by Read.ai; one workflow uses it for idempotency, another doesn't. Data shape varies by source.
- **The string vs number ID.** Slack sends `"user_id": "U123"`; the portal expects a number. Works fine until a payload doesn't quote.
- **The timezone mismatch.** Read.ai sends `meeting_start` in UTC; the portal renders as local; staff see meetings at "11pm" that were actually at 11am.
- **The silent additive change.** Producer adds an optional field. Consumer ignores. Six weeks later, the field becomes required for a feature, consumer wasn't updated, the feature breaks.
- **The test fixture from 2024.** Test passes because it uses an old fixture; production payload has moved on.

# Anti-Patterns

- "JSON.parse and trust." Always validate at the boundary.
- Sharing types between producer and consumer "for convenience" — they're in different codebases / repos. Use a schema definition as the contract, code-generated to types where possible.
- Treating schema changes as bug fixes (no version bump). Consumers can't tell the difference.
- Hardcoding URLs and webhook secrets in the producer for "testing" and forgetting.
- Using one Zod schema for multiple producers because "the shape is similar" — they will drift.

# Output Format

1. **Executive summary** — one paragraph: how many contracts in QUAY, how many formalized, top three risks.
2. **Contract inventory table** — producer, consumer, payload, schema-location, version, idempotency.
3. **Audit results per contract** — checklist with pass/fail.
4. **Findings table** — contract, gap, severity, fix.
5. **Severity** per rubric.
6. **Evidence** — schema files (or absence), example payload diff between producer and consumer.
7. **Recommended fix** — usually: write a Zod schema at `schemas/X.ts`, version it, validate at the n8n trigger / handler entry, add a test fixture.
8. **Implementation complexity** — `small` per contract; `medium` if schema needs to be inferred from existing production data.
9. **Owner/surface affected** — `integration-contract`, plus producer + consumer surface tags.
10. **Follow-up questions** — about acceptable versioning approach (Accept-Version header, payload `version` field, URL paths).

# Example Prompt

> Audit QUAY's cross-system contracts per `skills/quay/genius-team/integration-contract-reviewer/SKILL.md`. Produce the contract inventory and per-contract audit. Identify all schema drift, missing idempotency keys, undocumented headers, timestamp inconsistencies. Emit findings per `FINDINGS_SCHEMA.md`. Do not modify any schemas. Append to current audit board.

# Related Skills

- [n8n-workflow-reliability-engineer](../n8n-workflow-reliability-engineer/SKILL.md) — most contract violations show up in n8n.
- [data-lifecycle-governor](../data-lifecycle-governor/SKILL.md) — canonical sources match contract producers.
- [adversarial-operations-reviewer](../adversarial-operations-reviewer/SKILL.md) — unsigned webhooks and replayable payloads.
- [observability-telemetry-architect](../observability-telemetry-architect/SKILL.md) — schema-rejection metrics surface drift early.
