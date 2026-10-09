# Findings Schema

Every finding produced by any Genius-Team skill conforms to this schema. One finding = one Markdown file at `audits/<date>-<mode>/findings/<id>.md`.

## Required fields

```yaml
---
id: F-001                       # F-<3-digit sequential>, unique within the audit
title: <imperative, one line>   # "Founders can see other cohorts' tasks", not "Issue with tasks"
severity: P0                    # P0 | P1 | P2 | P3 — see rubric below
category: <category>            # see categories list below
surface:                        # one or more surface tags
  - portal-client
  - supabase
affected:                       # concrete artifacts — required
  files:
    - path/to/file.ts:120-145
  workflows:
    - n8n/readai-ingest/node-7
  tables:
    - public.tasks
  handlers:
    - slack-bot:proposal_submit
emitted_by: <skill-folder-name> # e.g. multi-tenant-boundary-architect
detected_at: <YYYY-MM-DD>
status: proposed                # proposed | accepted | deferred | waived | merged
merged_from: []                 # finding IDs this absorbed during dedup
defer_until: null               # YYYY-MM-DD if deferred
waived_until: null              # YYYY-MM-DD if waived
waiver_approver: null
---

# Evidence
<concrete observation — file:line, log line, query result, screenshot reference. Must be reproducible.>

# Why it matters
<one paragraph — what breaks, for whom, when, and how badly. Justifies the severity.>

# Likely failure mode
<the failure pattern this enables — "data leak", "silent drop", "infinite retry", "trust loss", etc.>

# Recommended fix
<concrete, scoped fix. Cite the file/table/workflow that changes. "Add RLS policy X to public.tasks" beats "improve security on tasks.">

# Implementation complexity
<trivial | small | medium | large> + one-line reason

# Dependencies
<other finding IDs this depends on, external blockers, decisions required>

# Owner
<human name or "unassigned">

# Follow-up questions
<questions for the team — bullet list — that affect how to fix this>

# Do-not-fix-yet
<optional — if you found this but it should NOT be fixed in the next sprint, explain why. e.g. "fixing this requires a Supabase migration that breaks an in-flight feature">
```

## Severity rubric

Severity is **not** opinion. Use this rubric.

### P0 — blocker

A finding is P0 if **any** of these are true:

- There is an active or imminent data leak across tenant boundaries.
- A credential (Supabase service-role, Slack bot token, AI key, service account JSON) is committed, logged, or reachable by an unprivileged user.
- The platform is in a state where a non-staff user can reach staff-only data or actions.
- A failure path silently drops user-submitted data with no detection.
- Handoff is blocked: no one but Ryan can perform a routine operational task that recurs.
- A workflow can recur or loop indefinitely on bad input (cost or correctness DoS).
- An AI artifact is making real decisions affecting humans without any human gate.
- An audit run has previously deferred this finding twice — automatic escalation.

P0 maximum: 5 per audit. If you would name a 6th, downgrade something or document why this audit is exceptional.

### P1 — serious

A finding is P1 if **any** of these are true:

- A failure is detectable but recovery is manual and undocumented.
- A boundary exists but isn't enforced — it relies on UI hiding, not RLS or auth.
- A schema mismatch can produce wrong data on the next release.
- An AI artifact has no token budget cap, no caching, and is reachable by a producer that can fire it in a loop.
- A surface (Slack, portal, n8n) writes to canonical storage with no idempotency key.
- A lifecycle state exists implicitly but isn't modeled (e.g., a "stale founder" with no defined transition).
- A runbook gap: a recurring operational task has no documented procedure.

### P2 — important

A finding is P2 if **any** of these are true:

- A pattern works but is fragile (would break under modest load, modest scope changes, or a junior engineer).
- An observability gap that doesn't prevent operation but delays incident detection.
- A code path is duplicated across two surfaces and will drift.
- A UX flow that confuses users but doesn't lose data.
- A cost line item that is non-critical but trending wrong.

### P3 — polish

Genuinely nice-to-have. Better naming, dead code removal, doc cleanup, ergonomic improvements with no operational impact.

## Categories

Use one of these. If nothing fits, propose a new category in your finding and flag it for the orchestrator.

- `auth` — authentication, sessions, role assignment, login surfaces
- `boundary` — tenant/cohort/org boundary, RLS, scope leakage
- `lifecycle` — state transitions, stale state, terminal-state handling
- `data-governance` — canonical source, retention, deletion, audit logs
- `ai-governance` — token spend, prompt versioning, hallucination, human gates
- `workflow-reliability` — n8n retries, idempotency, DLQ, partial failures
- `integration-contract` — schema, headers, idempotency keys, versioning
- `observability` — dashboards, alerts, logs, metrics
- `security-privacy` — least privilege, PII, secrets, compliance
- `ux-trust` — clarity, confidence, recoverability, decision support
- `adversarial-ops` — abuse, misuse, social/legal risk
- `qa-scenario` — sad-path, edge case, race condition
- `economics` — cost-to-operate, ROI, scaling risk
- `handoff-maintainability` — docs, runbooks, ownership, bus factor
- `product-scope` — kill, defer, do-now-vs-later
- `emergency` — reserved for in-progress incidents discovered during audit
- `skill-gap` — meta-finding: a Genius-Team skill missed something

## Surfaces (controlled vocabulary)

- `slack-bot`
- `portal-internal`
- `portal-client`
- `n8n`
- `supabase`
- `drive`
- `sheets`
- `readai`
- `ai`
- `docs`
- `cross-surface`

A finding may have multiple surface tags. `cross-surface` is required if ≥ 2 surfaces are affected.

## ID convention

- Findings: `F-001`, `F-002`, … sequential within one audit.
- Tasks: `T-001`, `T-002`, … sequential within one audit.
- IDs are not reused across audits. If F-010 from audit A reappears in audit B, audit B opens its own ID and notes `previously: <audit-A>/F-010` in the finding body.

## Anti-patterns in findings

- **Vague titles.** "Auth is sketchy" — useless. Required: a concrete, falsifiable statement.
- **No evidence.** A finding without a file:line or workflow-node reference is conjecture, not a finding.
- **No recommended fix.** "We should think about this" is not a fix. Either propose one or downgrade to an `unresolved_question` on the board.
- **Severity inflation.** Marking polish as P1 to get attention. The board loses signal.
- **Duplicate findings.** Two skills caught the same issue; the orchestrator must merge them — see `ORCHESTRATION.md` "Deduplication".
- **Findings that recommend "more documentation" as the entire fix.** Documentation is part of the fix, not the whole fix, unless the finding is specifically a runbook gap.

## Example — good finding

```yaml
---
id: F-007
title: Tasks table is readable by any authenticated user across cohorts
severity: P0
category: boundary
surface:
  - supabase
  - portal-client
affected:
  files:
    - supabase/migrations/2026_03_15_create_tasks.sql:1-40
  tables:
    - public.tasks
emitted_by: multi-tenant-boundary-architect
detected_at: 2026-05-28
status: proposed
---

# Evidence
`supabase/migrations/2026_03_15_create_tasks.sql` creates `public.tasks` with no RLS policy. A `SELECT * FROM tasks` from any authenticated session returns all rows. Verified by running the query against a non-staff JWT in Supabase Studio.

# Why it matters
Founders authenticated to the client portal can query the tasks table directly via the Supabase JS client. They can see other cohorts' tasks, including potentially private notes attached to those tasks. This is a tenant-boundary breach.

# Likely failure mode
Data leak across cohorts. Trust loss with the first multi-cohort client. Possible legal exposure if NDA-covered notes are attached.

# Recommended fix
Enable RLS on `public.tasks`. Add a SELECT policy: `auth.uid() in (select user_id from cohort_members where cohort_id = tasks.cohort_id)`. Add equivalent INSERT/UPDATE/DELETE policies. Add an integration test that asserts a non-member JWT cannot read another cohort's tasks.

# Implementation complexity
small — one migration, four policies, one test

# Dependencies
Requires `cohort_members` table to be populated (see F-008).

# Owner
unassigned

# Follow-up questions
- Should staff JWTs have an override? (Probably yes via `role = 'staff'` claim.)
- Are there any external integrations querying tasks with the service-role key that would be affected? (Check n8n credentials.)

# Do-not-fix-yet
n/a
```

## Example — bad finding (do not emit)

```yaml
---
id: F-099
title: Improve security
severity: P1
category: security-privacy
---

# Evidence
The app feels insecure in places.

# Why it matters
Security is important.

# Recommended fix
Audit the codebase and harden things.
```

This is conjecture, not a finding. Reject and re-emit specific findings against specific surfaces.
