# Implementation Task Schema

Every accepted finding that requires code or config change is converted into one or more tasks. Tasks live at `audits/<date>-<mode>/tasks/<task_id>.md`.

A task is **executable** — it has everything a future Claude Code session (or human engineer) needs to do the work without re-reading the audit.

## Required fields

```yaml
---
task_id: T-001                       # T-<3-digit sequential>, unique within the audit
source_finding_id:                   # one or more F-xxx
  - F-001
task_title: <imperative, one line>   # "Enable RLS and SELECT policy on public.tasks"
priority: P0                         # inherits from source finding's severity
estimate: 4h                         # h | d (hours or days), conservative
affected_area:                       # which surfaces this touches
  - supabase
  - portal-client
risk_level: low                      # low | medium | high — how much could go wrong
status: proposed                     # proposed | accepted | in-progress | done | abandoned
owner: <name or "unassigned">
created_at: <YYYY-MM-DD>
---

# Objective
<one paragraph — what this task changes about the system, in plain language. No engineer-speak unless necessary.>

# Acceptance criteria
<bulleted, testable statements. Each starts with "Given… when… then…" OR is a checkable assertion. No vague criteria.>
- Given a non-staff JWT, when `SELECT * FROM tasks` is run, then the returned set contains only rows where `cohort_id` matches a row in `cohort_members` for that user.
- Given a staff JWT (role claim = 'staff'), when the same query runs, then all rows are returned.

# Files likely changed
<concrete file paths. May add more during implementation but should be > 80% correct here.>
- `supabase/migrations/2026_05_28_tasks_rls.sql` (new)
- `supabase/tests/tasks_rls.test.sql` (new)
- `supabase/seed.sql` (modify: ensure test cohort_members row exists)

# Tests required
<what proves this works. Be specific. If no test exists, write one first.>
- New SQL test asserts the cross-cohort SELECT returns zero rows.
- Existing portal-client integration test for `/api/tasks` still passes.
- Add an e2e test: log in as Founder A, attempt to load Founder B's task by UUID — expect 404.

# Rollback plan
<how to undo this safely if it breaks production. If the change is one-way, say so explicitly.>
- Run a down-migration that drops the RLS policies and disables RLS on `public.tasks`. This restores the (broken) prior behavior, which is acceptable as a rollback only because the prior state was the production state at the time of the audit.
- No data is changed; only policy DDL.

# Dependencies
<other task IDs or external blockers>
- Requires T-005 (populate cohort_members for existing rows) to be done first.

# Out of scope
<things this task does NOT do, even if tempting to bundle>
- Does not refactor the tasks schema. Does not change RLS on adjacent tables (proposals, mentor_intros) — see F-008 for those.

# Verification by a human
<after Claude Code applies the change, what must a human verify by hand>
- Log into the client portal as a real founder. Confirm only their cohort's tasks are visible.
- Open the internal portal as staff. Confirm all tasks visible.
- Check Supabase logs for any RLS-denied queries from n8n that need a service-role bypass.

# Notes for the implementer
<free-form, optional. Use sparingly. Mention any subtle constraints.>
- The Supabase JS client must be initialized in the client portal with the user's JWT, not the anon key, for RLS to take effect on reads. Confirm `lib/supabase/client.ts` does this before declaring the task complete.
```

## Why this schema exists

The audit board is read by a human. The tasks are read by **future Claude Code sessions** (or junior engineers) who weren't in the original audit. They need:

- One file with everything in it.
- No "see the finding for context" — context is duplicated into the task on purpose. The task is self-contained.
- Falsifiable acceptance criteria — so a future session can know when it's done.
- A rollback plan — so a future session understands the blast radius.

## Acceptance criteria rules

- **Each criterion is testable.** "The UI feels better" is not testable. "The page renders in < 200ms p95 measured from devtools" is.
- **Each criterion can be checked independently.** A criterion that is "all the other criteria pass" is not a criterion.
- **No criterion describes implementation.** "Use a JOIN instead of a subquery" is implementation, not acceptance. Acceptance is about outcomes.

## Estimates

Be conservative. The estimate is the **upper bound** of how long a focused engineer would take, including writing tests and verifying. Heuristic:

- `trivial` finding → 1h–2h
- `small` finding → 2h–4h
- `medium` finding → 1d–2d
- `large` finding → 3d–5d → almost always should be split into multiple tasks

A task estimated `> 2d` is suspicious. Split it.

## Risk levels

- `low` — change is local, easy to verify, reversible in seconds.
- `medium` — change spans surfaces or affects shared state; rollback is possible but takes deliberate steps.
- `high` — change is one-way (e.g., data deletion, schema removal), or could affect external users. Must have explicit sign-off in the task body before execution.

## Anti-patterns in tasks

- **Vague title.** "Fix auth" is not a task. "Add invite-token expiry to the founder invite flow, default 7 days, expired tokens return 410" is.
- **No acceptance criteria.** A task without checkable outcomes is a wish.
- **No rollback plan.** Even "this is one-way, no rollback possible" is acceptable if explicit. Silence is not.
- **Too big.** A task that touches > 10 files or > 1 surface is probably two tasks.
- **Bundled improvements.** "While I was in there I also refactored X" — no. Out of scope. Open a new finding if X needs work.
- **Self-modifying scope.** "Implement Y, and if Y is hard, do Z instead." Pick one. If both are real, two tasks.

## Conversion rules from findings

- Every accepted P0 finding → ≥ 1 task. P0 with no task = audit incomplete.
- Every accepted P1 finding → 1 task.
- P2 findings → task only if estimate ≤ 4h; else go to defer list.
- P3 findings → not converted by default. Pull individually if/when prioritized.
- Multiple findings can collapse into one task if the fix is genuinely the same change. List all source IDs in `source_finding_id`.
- One finding may expand into multiple tasks if the fix spans surfaces. Each task lists the same `source_finding_id`.

## Example — converting a finding to a task

Finding `F-007` (RLS missing on tasks) becomes:

- `T-001` — Enable RLS and SELECT policy on `public.tasks`.
- `T-002` — Populate `cohort_members` table for existing rows.
- `T-003` — Add e2e test: cross-cohort task access returns 404.

`T-001` depends on `T-002`. `T-003` depends on both.

This is normal. One P0 finding routinely produces 2–4 tasks. The board shows the relationship.

## How a future Claude Code session uses a task

```
Read skills/quay/genius-team/audits/<audit>/tasks/T-001.md.

Implement the task. Constraints:
- Stay within `affected_area`. Do not change adjacent files.
- Satisfy every acceptance criterion. If you can't satisfy one, stop and report which.
- Run the listed tests. Add the missing test if the file doesn't exist.
- Show the diff. Do not push, deploy, or modify env vars.
- If the task's risk_level is high, stop before applying and ask for explicit go-ahead.
```

That prompt is enough. The task file carries everything else.
