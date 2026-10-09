---
name: quay-lifecycle-state-machine-auditor
description: Forces every domain object in QUAY (founder, mentor, cohort, proposal, intro, transcript, workflow run, account) to have an explicit lifecycle — states, transitions, terminal states, reactivation rules, and behavior on stale state.
---

# Purpose

Most QUAY entities have implicit lifecycles: "active" until "not active anymore." This is fine until a founder finishes a cohort, a mentor stops responding, a proposal sits unanswered for two months, an n8n workflow run dies mid-execution, or a transcript ingestion stalls. Then nobody knows what state the system is in.

This skill produces an **explicit state machine** for every domain object: states, allowed transitions, illegal transitions, terminal states, reactivation rules, and what happens to dependent data when a state changes.

# When to Use

- During a full or handoff audit.
- When adding a new domain object (e.g., introducing "client institution" or "external advisor").
- When a "weird state" incident occurs (founder still receiving surveys after cohort ended, proposal stuck in "submitted" for 60 days, mentor showing as active but actually offboarded).
- Before exposing any object's state to non-staff users — implicit state is fine when only staff see it; founders need a real status.

# Expected Inputs

1. Supabase schema (tables, enums, status columns).
2. Any explicit state column or enum (`status`, `state`, `stage`, `lifecycle_stage`).
3. The code that mutates those columns — RPCs, n8n nodes, app routes, Slack handlers.
4. Product docs that describe "a founder's journey" / "a cohort's flow" / "what happens when a proposal is submitted."

# Required Context to Inspect

- `supabase/migrations/*.sql` — every table that has a status-like column.
- All Supabase RPCs that change status (`grep -r "status\s*=\|status:\s" supabase/`).
- n8n workflows that update Supabase rows.
- Cron jobs or scheduled flows (these are usually where stale-state recovery would live, if it existed).
- `skills/quay/activity-feed-model/SKILL.md` — the activity feed records transitions; the model should align.

# Review Methodology

For each domain object, produce the following four artifacts. Anything missing or wrong is a finding.

## 1. State catalog

List every state the object can be in. Include:
- The state name.
- Whether the state is **observable** to the user (or only to staff/the system).
- How long the object is *expected* to stay in this state.
- What is true about the object only when it's in this state (e.g., "only `active` founders receive weekly surveys").

## 2. Transition diagram

For each pair of states, declare:
- **Allowed** transitions, with the trigger (event, time, manual action).
- **Illegal** transitions (e.g., a `deleted` founder cannot become `active` again; a `submitted` proposal cannot return to `draft`).
- **Idempotent** transitions (re-running the same transition is safe).

## 3. Terminal-state behavior

- Which states are terminal (no transitions out)? `cohort.completed`, `founder.alumni`, `mentor.removed`, `proposal.archived`?
- For each terminal state, what is the data-retention rule? Are the rows kept, archived, anonymized, or deleted?
- Is the terminal state distinguishable from a stale-pending state? (Critical: an unanswered proposal "submitted" for 6 months is NOT a terminal state — it's a bug.)

## 4. Stale-state and recovery behavior

- For every non-terminal state, what's the expected max dwell time?
- What triggers a re-check or escalation if the object exceeds it?
- What's the rollback or retry behavior if a transition fails partway (e.g., n8n flow that updates Supabase + posts to Slack — only the Supabase update lands)?
- Is there reactivation? E.g., a founder who completed a cohort and rejoins a later one — same row, new row, or linked rows?

# Severity System

- **P0** — A terminal state can be re-entered, putting the system in an undefined state (e.g., a "deleted" user that re-appears as "active" because of a stale Slack handler). Or: a state mutation is not atomic with its dependent writes and can silently fail half-way.
- **P1** — A state exists implicitly (a column is empty/null) without a name or transition rules. Stale-state recovery is undefined for an object users see.
- **P2** — Transitions exist but aren't audited (no activity event, no log). Or: two state columns describe the same thing and can diverge.
- **P3** — State names are inconsistent across tables (`active` vs `enabled` vs `live`). Cosmetic but creates handoff confusion.

# Checklist

For each domain object below, an explicit state machine exists:

- [ ] **Founder** — invited, active (in-cohort), on-pause, alumni, removed.
- [ ] **Mentor** — prospect, onboarded, active, paused, removed.
- [ ] **Cohort** — planned, active, completed, archived.
- [ ] **Proposal** — drafted, submitted, under-review, approved, rejected, withdrawn, archived.
- [ ] **Mentor intro** — requested, scheduled, completed, declined, no-show, cancelled.
- [ ] **Transcript ingestion** — received, parsed, summarized, attached-to-meeting, failed, discarded.
- [ ] **Workflow run** — queued, running, succeeded, failed, retrying, dead-lettered, manually-resolved.
- [ ] **Account/session** — see `auth-identity-architect`; should be modeled here too.
- [ ] **Activity event** (if mutable at all) — should likely be append-only with no lifecycle.

For each state machine:

- [ ] All states named.
- [ ] All transitions listed, with triggers.
- [ ] Illegal transitions explicitly noted (so future code doesn't accidentally allow them).
- [ ] Terminal states identified, with retention rule.
- [ ] Stale-state max dwell time defined.
- [ ] Recovery rule defined for failed transitions.
- [ ] Every transition emits an `activity_event` (per `quay-activity-feed-model`).

# QUAY-Specific Questions

- A founder who attended week 1 then ghosted — what state? Is "ghosted" different from "removed"? Is there a "lapsed" state?
- A cohort with no active founders — should the cohort auto-archive, or stay active "in case someone returns"? What's the rule?
- A proposal "submitted" 60 days ago with no decision — is that a stale state or terminal? Does the founder still see it as "pending"?
- A mentor who hasn't done an intro in 6 months — paused, removed, or "warm bench"? Different states have different visibility.
- A Read.ai transcript whose meeting can't be matched to a known cohort meeting — what state? Discarded? Quarantined? Manually-triaged?
- An n8n workflow run that fails on the third retry — where does it go? A `dead_letter` table? An ops Slack channel? A bug tracker? Currently the answer is probably "nowhere."
- A founder who finishes Cohort 3 and re-applies to Cohort 5 — same row with state transitions, or new row linked to old? (Strong recommendation: linked-rows pattern, so cohort history is immutable per cohort.)

# Common Failure Modes

- **Implicit "active" via NULL.** No status column; "active" means "exists and not deleted." This conflates "active" with "exists" and breaks the moment you need a non-active-but-not-deleted state.
- **Status enum without a `transitions_allowed` rule.** Any code can set any status; nothing prevents going from `archived` back to `draft`.
- **Two status columns.** `status` and `state` on the same table, drifting independently.
- **No stale recovery.** Proposals submitted forever. Workflows "running" for days. No cron, no escalation, no surfacing.
- **Soft-delete that doesn't filter.** A `deleted_at` column exists but half the queries don't include `WHERE deleted_at IS NULL`.
- **Rejoin not modeled.** A founder who completes one cohort and joins another either gets duplicated, or their history is destroyed.

# Anti-Patterns

- "We'll add states later when we need them." Later, the table is full of rows in undefined states, and you can't backfill what they were supposed to be.
- Storing state in two places (app + n8n) and trying to keep them in sync via webhooks.
- A `is_active` boolean instead of an enum, then needing a third state and adding `is_paused` next to it, then `is_archived`. Use enums from the start.
- Recovery logic that lives in a Slack handler ("if the user clicks this button, reset the state to X").

# Output Format

Per finding (`FINDINGS_SCHEMA.md`). Plus, the audit deliverable from this skill includes:

1. **Executive summary** — one paragraph: which objects have explicit state, which don't, which are dangerous.
2. **Findings table** — object, missing/incorrect element (state, transition, terminal, recovery), severity.
3. **Severity** — per rubric.
4. **Evidence** — schema file:line, RPC code, n8n node, real example row in undefined state.
5. **Recommended fix** — usually one of: (a) add an enum column with a defined set, (b) write a state-machine doc + migration, (c) add a cron/escalation job for stale state, (d) add a transition guard in the RPC.
6. **Implementation complexity** — `small` for adding an enum; `medium` for backfilling states; `large` for redesigning soft-delete patterns retroactively.
7. **Owner/surface affected** — almost always includes `supabase`; often also `n8n` (recovery) and the surface that displays the state.
8. **Follow-up questions** — product intent ("what is 'paused' supposed to mean for a founder?").
9. **"Do not fix yet"** — for objects whose lifecycle is genuinely uncertain because the product hasn't decided yet. Flag for `product-scope-ruthless-prioritizer` to decide.

# Example Prompt

> Audit lifecycles for every QUAY domain object per `skills/quay/genius-team/lifecycle-state-machine-auditor/SKILL.md`. Produce a state machine for each object in the checklist. Emit findings for missing states, missing transitions, undefined terminal behavior, and undefined stale-state recovery. Cite schema and code. Do not change any code or schema. Append to current audit board.

# Related Skills

- [data-lifecycle-governor](../data-lifecycle-governor/SKILL.md) — once states are defined, where does data live across each state.
- [n8n-workflow-reliability-engineer](../n8n-workflow-reliability-engineer/SKILL.md) — workflow-run lifecycle and dead-letter handling.
- [observability-telemetry-architect](../observability-telemetry-architect/SKILL.md) — surfacing stale-state objects as operational alerts.
- [auth-identity-architect](../auth-identity-architect/SKILL.md) — account lifecycle is a subset.
