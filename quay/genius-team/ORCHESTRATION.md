# Genius-Team Orchestration

How the sixteen Genius-Team skills coordinate to produce a single, actionable audit board — not sixteen separate reports.

## Core principles

1. **One audit run → one audit board.** Every run produces a single file shaped per `AUDIT_OUTPUT_TEMPLATE.md`. Skills contribute findings to that board; they don't emit free-floating documents.
2. **Findings, not narratives.** Every contribution is a structured finding per `FINDINGS_SCHEMA.md`. If a skill wants to "discuss" something, it becomes an `unresolved_question` on the board, not prose.
3. **Sequence matters.** Skills run in a defined order so later skills can build on earlier findings instead of duplicating them. See **Run order** below.
4. **Dedup before scoring.** Two skills often catch the same thing from different angles. The orchestrator merges them into one finding with combined evidence before assigning severity.
5. **Severity is conservative.** Inflation kills the board. P0 means production-or-handoff-broken. See `FINDINGS_SCHEMA.md`.
6. **Findings die or become tasks.** No finding survives an audit without a decision: accepted (→ task), deferred (with date), or waived (with reason). The board has no permanent "TODO" bucket.

## Audit modes

Each mode lists the skills it runs, in order, and the kind of board it produces.

### `full` — full platform audit
Run when: scoping a major release, preparing handoff, or no audit has been run in 60+ days.

Skills, in order:
1. `institutional-pm-reviewer` (frames what the platform claims to do)
2. `multi-tenant-boundary-architect` (org/cohort/founder boundaries)
3. `auth-identity-architect` (who can be who)
4. `lifecycle-state-machine-auditor` (what state can things be in)
5. `data-lifecycle-governor` (where data lives, who can touch it)
6. `integration-contract-reviewer` (schemas between surfaces)
7. `n8n-workflow-reliability-engineer` (retries, idempotency, DLQ)
8. `ai-governance-cost-optimizer` (token spend, hallucination, gates)
9. `observability-telemetry-architect` (can we see what's happening)
10. `security-privacy-compliance-reviewer` (least privilege, PII, audit logs)
11. `adversarial-operations-reviewer` (abuse cases, misuse, social risk)
12. `institutional-qa-scenario-simulator` (sad paths, edge cases)
13. `enterprise-ux-psychologist` (does the UI help anyone make decisions)
14. `platform-economics-analyst` (what does this cost to run)
15. `handoff-maintainability-engineer` (can QUAY maintain this without Ryan)
16. `product-scope-ruthless-prioritizer` (P0/P1/P2/P3 + kill list)

Expected output: full board with 40–80 findings, ~15–25 accepted tasks, kill list, deferred list, handoff risk register.

### `quick` — 60-minute read on platform health
Run when: weekly cadence, after a sprint, or before a stakeholder demo.

Skills, in order:
1. `institutional-pm-reviewer`
2. `adversarial-operations-reviewer`
3. `institutional-qa-scenario-simulator`
4. `product-scope-ruthless-prioritizer`

Expected output: ~10–20 findings, P0/P1 only, focused on "what's demo-grade vs operational" and "what to cut."

### `pre-deploy` — before promoting a branch to staging/prod
Run when: any merge to a deploy-tracked branch.

Skills, in order:
1. `integration-contract-reviewer`
2. `n8n-workflow-reliability-engineer` (only if n8n touched)
3. `auth-identity-architect` (only if auth/role code touched)
4. `security-privacy-compliance-reviewer`
5. `institutional-qa-scenario-simulator` (regression scenarios for changed surfaces)

Expected output: pass/fail board. Any P0 blocks the deploy. P1s become "must-do this week" tasks.

### `handoff` — Ryan is leaving, can QUAY maintain this
Run when: internship/contract end is within 30 days, or onboarding a new engineer.

Skills, in order:
1. `handoff-maintainability-engineer` (frames the bus-factor risk)
2. `auth-identity-architect` (no one wants to inherit broken auth)
3. `multi-tenant-boundary-architect` (no one wants to inherit a leak)
4. `data-lifecycle-governor` (no one wants to inherit "where does X live?")
5. `n8n-workflow-reliability-engineer` (workflows are the hardest to inherit)
6. `security-privacy-compliance-reviewer`
7. `observability-telemetry-architect` (can the new operator see anything)
8. `product-scope-ruthless-prioritizer` (kill list + handoff-critical list)

Expected output: handoff risk register, runbook gap list, ownership map, P0 "fix before handoff" tasks.

### `n8n-only` — workflow audit
Run when: a flow misbehaves, a new flow is added, or n8n bills spike.

Skills, in order:
1. `n8n-workflow-reliability-engineer`
2. `integration-contract-reviewer`
3. `observability-telemetry-architect`
4. `ai-governance-cost-optimizer` (only if AI calls in the flow)
5. `platform-economics-analyst` (only if cost-driven)

### `auth-security` — auth + boundary + privacy
Run when: adding a new role, a new surface, or onboarding clients.

Skills, in order:
1. `auth-identity-architect`
2. `multi-tenant-boundary-architect`
3. `security-privacy-compliance-reviewer`
4. `adversarial-operations-reviewer`
5. `lifecycle-state-machine-auditor` (account/session lifecycle)

### `ai-cost` — AI governance + spend
Run when: token bill is rising, new AI feature is proposed, or before opening AI to clients.

Skills, in order:
1. `ai-governance-cost-optimizer`
2. `platform-economics-analyst`
3. `observability-telemetry-architect`
4. `enterprise-ux-psychologist` (do users trust the AI output)
5. `adversarial-operations-reviewer` (prompt injection, abuse)

## Run order rationale

PM-level skills run first because they frame **what the platform is supposed to do**. Auth, boundary, and lifecycle skills run next because they define **who can do what to what**. Integration and reliability skills then check **the wires**. Observability and AI-cost check **what we can see and what it costs**. UX and adversarial skills check **what users actually do**. QA simulates **the sad paths**. Economics asks **whether the math works**. Handoff and prioritization run last because they need every earlier finding to triage correctly.

A later skill that finds something an earlier skill should have caught **flags the earlier skill's gap** — that's a meta-finding tagged `category: skill-gap`.

## Deduplication

Two findings are duplicates when:
- They cite the same evidence (same file path / workflow node / table) **AND** point at the same root cause.
- OR: they describe symptom and cause of the same defect (e.g., "founders see other founders' tasks" + "RLS missing on tasks table").

The orchestrator merges duplicates into one finding:
- `title` is taken from the more specific/root-cause finding.
- `evidence` is the union of both.
- `severity` is the **higher** of the two.
- `surface` is the union.
- The merge is noted in the finding's `dependencies` field: `merged_from: [skill-x, skill-y]`.

If two findings cite the same evidence but propose **conflicting fixes**, do not merge — they become a `decision_required` entry on the board with both proposals.

## Severity assignment

Each skill proposes a severity using the P0–P3 system in `FINDINGS_SCHEMA.md`. The orchestrator may upgrade or downgrade based on:

- **Upgrade triggers**: production-affecting, multi-surface impact, security/privacy implication, handoff-blocking, recurring (already seen in a prior audit).
- **Downgrade triggers**: behind a feature flag, only-staff-visible, mitigated by an existing manual process, single-user impact.

Severity is recorded with a one-line justification in the finding's `why_it_matters` field. **No bare severities.**

## From findings to tasks

The audit board is not the work. Tasks are.

Conversion rules:
- Every **accepted** P0 and P1 finding **must** become at least one task (per `IMPLEMENTATION_TASK_SCHEMA.md`).
- P2 findings become tasks if they are small (≤ 2 hours), otherwise they go on the deferred list with a target sprint.
- P3 findings go on the polish list and are never carried into a sprint unless explicitly pulled.
- A single finding may produce multiple tasks if the fix spans surfaces — link them via `source_finding_id`.
- A task is **not** created without acceptance criteria. "Improve X" is not a task; "X must do Y, verified by Z" is.

## Avoiding infinite planning

The single most common failure mode of an audit system is generating more analysis instead of more shipped code. Defenses:

1. **One board per run, not one per skill.** Skills contribute findings; they do not produce their own reports.
2. **A skill that cannot find anything outputs `no_findings: true` and stops.** It does not invent things to look productive.
3. **Maximum 5 P0 findings per audit.** If a skill proposes a 6th, it must downgrade something or justify the inflation.
4. **Every accepted finding becomes a task in the same session.** No "we'll convert these later."
5. **The board is timestamped and immutable after acceptance.** Subsequent audits produce new boards; they do not edit prior ones.
6. **If a finding has been on three consecutive boards without being shipped, it is either critical (escalate to P0) or not real (kill it).** No zombie findings.
7. **No skill is allowed to recommend "create more documentation" as its primary fix more than once per audit.** Documentation gaps are real, but a wall of new docs is a sign the team is avoiding the actual work.

## Coordination across surfaces

The Genius Team has to think across **all** QUAY surfaces, not just one. Surface tags on each finding:

- `surface: slack-bot` — the proposals/surveys bot
- `surface: portal-internal` — staff dashboard
- `surface: portal-client` — founder/client portal
- `surface: n8n` — orchestration flows
- `surface: supabase` — schema, RLS, RPCs
- `surface: drive` — Google Drive folder structure / permissions
- `surface: readai` — transcript ingestion
- `surface: sheets` — Google Sheets canonical stores
- `surface: ai` — model calls, prompts, artifact storage
- `surface: docs` — runbooks, handoff docs, ADRs
- `surface: cross-surface` — touches ≥ 2 surfaces

Cross-surface findings (`surface: cross-surface`) are inherently more dangerous because no single owner can fix them alone — they get a +1 severity bump unless explicitly justified otherwise.

## How to actually run an audit

Inside a Claude Code session pointed at the QUAY repo (or QUAY docs working tree):

```
Run a Genius-Team `<mode>` audit per skills/quay/genius-team/ORCHESTRATION.md.

Use these skills in order, contributing findings to ONE audit board at
skills/quay/genius-team/audits/<YYYY-MM-DD>-<mode>/AUDIT.md per
AUDIT_OUTPUT_TEMPLATE.md.

For each finding, follow FINDINGS_SCHEMA.md.
After all skills run, dedup, score severity, and convert accepted P0/P1
findings into tasks per IMPLEMENTATION_TASK_SCHEMA.md, one task file per
task under tasks/<task_id>.md.

Constraints:
- Read-only inspection. Do not modify any platform code, n8n exports,
  Supabase schema, env files, or deploy config.
- Cite evidence (file:line, workflow node, table.column, Slack handler) on
  every finding. No vague findings.
- Maximum 5 P0 findings. If you exceed that, downgrade or justify.
- Stop after producing the board and tasks. Do not produce additional
  reports or "next-step" prose.
```

That prompt is the entire entry point. Everything else lives in the skill files.

## When a skill needs to escalate

If a skill discovers something **catastrophic** (active data leak, exposed credential, founders currently accessing other founders' data), it does not wait for the audit to finish. It:

1. Logs the finding as `severity: P0`, `category: emergency`.
2. Immediately outputs a one-line "STOP THE AUDIT" notice to the user.
3. Halts further skill execution until the user acknowledges.

This is the only path that interrupts the orchestrator.
