# QUAY Genius Team

A reusable senior-review layer for the QUAY OS platform. Sixteen specialized skills that together act as a virtual staff team — PM, staff engineer, QA lead, auth architect, data architect, AI governance lead, workflow reliability engineer, platform economist, security/privacy reviewer, enterprise UX researcher, and adversarial ops reviewer.

This is the layer that asks **"is this really institutional-grade, or just demo-grade?"** It complements the tactical skills already in `skills/quay/*` (architecture-review, supabase-schema, n8n-boundaries, etc.) by pushing on assumptions those skills take for granted.

## Why this exists

QUAY OS has shipped real surfaces — Slack bot, n8n flows, Drive ingestion, Read.ai pipeline, internal/client portals. But shipped ≠ institutional. Hidden gaps include:

- Auth that works in dev but isn't ready for two boundaries (staff vs founder vs client vs mentor).
- Lifecycle states that exist implicitly but aren't modeled (what is a "stale founder"? a "paused cohort"?).
- AI artifacts whose token cost, hallucination risk, and human-review gating are unspecified.
- n8n workflows without retry, idempotency, or observable failure paths.
- Drive folder structures with no canonical permission model.
- Internal-vs-client data boundaries enforced by hope rather than RLS.

The Genius Team exists to find and fix those gaps **before they become incidents** and before handoff.

## How to use it

1. **Pick an audit mode** from `ORCHESTRATION.md` (full / quick / pre-deploy / handoff / n8n-only / auth-only / AI-cost / adversarial).
2. **Run the orchestrator** — it sequences the relevant skills, gathers findings, deduplicates, and assigns severity.
3. **Get one audit board** following `AUDIT_OUTPUT_TEMPLATE.md` — P0/P1/P2/P3 findings, with each finding shaped per `FINDINGS_SCHEMA.md`.
4. **Convert findings to tasks** using `IMPLEMENTATION_TASK_SCHEMA.md` — every accepted finding becomes a concrete, scoped task with acceptance criteria and rollback plan.
5. **Act on the board, not the report.** Reports are read once; tasks ship.

## Recommended first run for QUAY OS

Start with the **Handoff Audit** in `ORCHESTRATION.md`. It runs the four most consequential reviewers (`auth-identity-architect`, `multi-tenant-boundary-architect`, `n8n-workflow-reliability-engineer`, `handoff-maintainability-engineer`) and produces a P0/P1 list focused on what would break if Ryan stopped touching the project tomorrow.

If you have an hour, run the **Quick Audit** (PM + Adversarial + QA Scenario + Prioritizer). It gives a fast read on which features are demo-grade vs operational, and what to cut before scaling.

If you have a day, run the **Full Audit** — all 16 skills, sequenced by `ORCHESTRATION.md`.

## How this complements existing `skills/quay/*`

| Existing skill | Genius-Team counterpart |
|---|---|
| `quay-architecture-review` | `institutional-pm-reviewer` + `multi-tenant-boundary-architect` (pressures the spine, doesn't just check drift) |
| `quay-supabase-schema` | `data-lifecycle-governor` + `lifecycle-state-machine-auditor` (asks "what's the lifecycle?", not just "is RLS on?") |
| `quay-n8n-boundaries` | `n8n-workflow-reliability-engineer` + `integration-contract-reviewer` (retries, DLQs, schema drift) |
| `quay-ai-feature-implementation` | `ai-governance-cost-optimizer` (token budget, hallucination policy, human gate rules) |
| `quay-deploy-push-checklist` | `handoff-maintainability-engineer` + `security-privacy-compliance-reviewer` |
| `quay-activity-feed-model` | `observability-telemetry-architect` (turns events into operational signal) |

Use the existing skills to **build**. Use the Genius Team to **pressure-test, audit, and prioritize**.

## Hard rules (inherit from parent QUAY rules + add)

- **These skills produce findings and tasks. They do not rewrite production code.** A skill that "fixed it itself" is broken — humans accept findings before code moves.
- **No secrets, no env modifications, no deploy commands, no force pushes** from any Genius-Team skill session.
- **Every finding cites evidence** (file path, n8n workflow node, table name, Slack handler) or it is not a finding.
- **Every finding has a recommended fix** — vague observations are anti-pattern (see `FINDINGS_SCHEMA.md`).
- **Severity is not opinion.** Use the P0–P3 system defined in each SKILL.md and in `FINDINGS_SCHEMA.md`. Inflation kills usefulness.
- **Don't generate endless reports.** Each audit run produces one audit board (per `AUDIT_OUTPUT_TEMPLATE.md`). If a follow-up is needed, it becomes a task on the board, not another report.

## Warning: findings ≠ rewrites

These skills are diagnostic. They produce:
- A prioritized list of real problems with evidence.
- A task schema you (or a future Claude Code session) can execute against.

They do **not**:
- Refactor the Slack bot, modify n8n workflows, alter Supabase schema, change deployment, or touch env vars.
- Create new product features beyond what's needed to close an identified gap.
- Generate code unless asked, and only inside a separate Claude Code session that scopes to one task at a time.

## Converting Genius-Team output into Claude Code implementation prompts

Each task produced by the Genius Team (per `IMPLEMENTATION_TASK_SCHEMA.md`) is shaped to drop directly into a fresh Claude Code session:

```
Read skills/quay/genius-team/audits/<latest-audit>/tasks/<task_id>.md.
Implement the task per its acceptance criteria.
Stay scoped to `affected_area`. Do not modify other surfaces.
Run the listed tests. If a test does not exist, write it first.
Show the diff before applying. Do not push or deploy.
```

The schema is designed so the implementer-session has every input it needs: title, objective, files, acceptance criteria, rollback. No re-reading of the original audit is required.

## Files in this folder

- `README.md` — this file
- `ORCHESTRATION.md` — audit modes, sequencing, dedup, severity, task generation
- `AUDIT_OUTPUT_TEMPLATE.md` — the one-page audit board format
- `FINDINGS_SCHEMA.md` — shape of every individual finding
- `IMPLEMENTATION_TASK_SCHEMA.md` — shape of every executable task
- `REFERENCE_FRAMEWORKS.md` — public references and prior art used
- `<skill-folder>/SKILL.md` — one per skill (16 total)
