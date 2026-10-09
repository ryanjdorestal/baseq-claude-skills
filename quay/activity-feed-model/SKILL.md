---
name: quay-activity-feed-model
description: Model the unified QUAY activity feed — one append-only stream that captures Slack, Read.ai, Drive, Monday, and portal events, with rules for compression and surface-specific projections.
---

# QUAY Event / Activity Feed Modeling

## Purpose

Define the canonical activity feed that powers staff dashboards, member portals, AI summaries, and search. One append-only stream of typed events, projected into surface-specific views. The feed is the platform's nervous system; every other surface reads from it.

## When to use

- Adding a new event source (a new Slack event type, a new n8n trigger, a new Drive watcher).
- Designing a feature that needs a chronological view of what's happened.
- Powering an AI summary that needs source events.
- Investigating whether something is being "double-recorded" across systems.

Do **not** use it for ephemeral UI state or analytics-only telemetry — that belongs in a separate sink.

## Expected inputs

1. **Event source** — Slack, Read.ai, Drive, Monday, portal action, AI-generated.
2. **Event type** — a stable name from the controlled vocabulary (see below).
3. **Subject + actor** — the member/mentor/staff/cohort the event is about, and who caused it.
4. **Payload** — typed schema; no `metadata: any`.
5. **Idempotency key** — every event has one, derived from the source.

## Canonical entity: `activity_events`

Columns:

- `id uuid pk`
- `occurred_at timestamptz not null` — when the thing actually happened, not when we recorded it.
- `recorded_at timestamptz not null default now()`
- `source` — enum: `slack`, `read_ai`, `drive`, `monday`, `portal`, `n8n`, `ai`, `system`.
- `event_type` — enum from the controlled vocabulary.
- `actor_kind`, `actor_id` — who caused it (`member`, `mentor`, `staff`, `system`, `ai`).
- `subject_kind`, `subject_id` — who/what it's about.
- `cohort_id` — denormalized for filtering.
- `payload jsonb` — validated against a Zod/JSON schema per `event_type`.
- `idempotency_key text unique not null`.
- `dedupe_of uuid null` — if this event is a duplicate, point at the original; do not delete.

## Controlled vocabulary (initial set)

- `member.joined_cohort`
- `member.submitted_doc`
- `member.missed_session`
- `mentor.session_scheduled`
- `mentor.session_completed`
- `mentor.note_added` (staff-only audience)
- `transcript.captured` (Read.ai)
- `doc.created`, `doc.updated`, `doc.shared` (Drive)
- `task.created`, `task.completed` (Monday)
- `slack.message_flagged` (only flagged ones — not every message)
- `ai.summary_generated`
- `staff.intervention_logged`

New event types are added by editing this list **and** the schema directory in one PR. No silent additions.

## Output format

For each new event integration:

1. **Event type schema** — Zod + JSON Schema in `schemas/events/<type>.ts`.
2. **Ingest path** — where the event enters (n8n node, webhook handler, server action) and how it's validated and deduped.
3. **Projection note** — which surfaces read this event and how it appears compressed (one line per event).
4. **Idempotency rule** — exact derivation of `idempotency_key`.
5. **Retention rule** — keep forever, or aged-out after N days.

## Compression rules (how surfaces show feed entries)

- Each `event_type` has a **one-line renderer** that takes the row and returns: `<who> <verb> <what> <when>`.
- Surfaces never show raw payload; always the renderer output.
- A surface may collapse runs (e.g. "5 docs updated in the last hour") — collapse logic is owned by the surface, not the feed.
- AI-generated summaries reference event ids (`source_event_ids[]`), never re-paraphrase from memory.

## Constraints

- Append-only. No `UPDATE` of an event after insert except setting `dedupe_of`.
- Idempotency-key unique constraint is the source of dedupe. No "let's add a window check" tricks.
- RLS: staff sees all; member sees only events where `subject_id = auth.uid()` *or* where the renderer is explicitly cohort-public.
- No PII in `payload` beyond what already lives on the subject row.
- The feed is *not* the analytics warehouse. Aggregations live in materialized views or a separate sink.

## Anti-patterns

- One mega-event type `generic_activity` with everything stuffed in `payload`.
- Storing the rendered string in the event row (renderers belong to surface code, not to the event).
- Using `recorded_at` for ordering — always order by `occurred_at`.
- Triggering side effects (Slack post, email) from inside a Supabase trigger on this table — that's n8n's job.
- AI calls that generate a summary and don't write a `dedupe_of` or `source_event_ids` reference back.

## Checklist

- [ ] Event type added to the controlled vocabulary list and the schema directory in the same PR.
- [ ] Schema validates incoming payloads at the ingest path.
- [ ] Idempotency key derivation is deterministic and documented.
- [ ] Renderer added in `lib/feed/renderers/<type>.ts`.
- [ ] RLS policy is named and tested.
- [ ] Retention rule documented.
- [ ] No side effects triggered from a Supabase trigger on `activity_events`.
- [ ] At least one consumer surface (dashboard, portal block, AI summary) is wired.

## Example prompt

> Add a `mentor.session_completed` event type to the QUAY activity feed per `skills/quay/activity-feed-model/SKILL.md`. Source: n8n workflow listening to Read.ai. Output the schema, ingest path, idempotency key derivation, renderer, and RLS policy update. Do not implement — produce the design diff only.
