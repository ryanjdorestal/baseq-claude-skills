---
name: quay-handoff-maintainability-engineer
description: Audits QUAY's readiness for someone other than Ryan to maintain it. Surfaces bus-factor risks, missing runbooks, undocumented setup, unowned components, and the gap between "Ryan can do it" and "any QUAY staff engineer can do it."
---

# Purpose

Right now, QUAY is heavily Ryan-dependent. That's expected during initial build. But the platform needs to survive Ryan's departure (or vacation, or just attention elsewhere). This skill audits the platform end-to-end from the perspective of a hypothetical "Engineer A" — a competent backend engineer who has never seen QUAY before — and identifies every place they would get stuck.

The output is a **handoff risk register**: a prioritized list of bus-factor concerns, each with a concrete remediation that ends in a doc, a runbook, a script, or a config change.

# When to Use

- Every full audit; every `handoff` audit.
- 30 days before any planned Ryan-absence period (internship end, leave, vacation).
- When onboarding a new staff engineer.
- Quarterly as routine hygiene.

# Expected Inputs

1. The codebase (all surfaces).
2. The `docs/` folder and any inline README files.
3. Setup instructions (or their absence).
4. Deployment configs and the team who can trigger them.
5. Each SaaS dependency and who has admin access.

# Required Context to Inspect

- Repo root `README.md` and any `docs/` directory.
- Setup scripts, `.env.example`, package.json scripts.
- Deployment configs (`vercel.json`, GitHub Actions, etc.).
- Existing skill files (`skills/quay/*`).
- All credential locations (per `security-privacy-compliance-reviewer`).
- The "who owns what" question for each surface.

# Review Methodology

Walk the audit through five concerns.

## 1. The "first day" path

Engineer A is given the repo URL and asked to run QUAY locally. Walk it step by step:

- Clone repo. Are the prerequisites stated (Node version, pnpm/npm, etc.)?
- `.env.example` complete? Every variable named with an explanation of where to get its value?
- `npm install` / `pnpm install` — works?
- DB setup: is there a script that initializes a local Supabase, or do they have to point at a shared dev project?
- Seed data: is there enough to develop against?
- Local n8n: is there a guide, or are they pointed at production n8n? (Production n8n is dangerous to develop against.)
- Slack: how do they test Slack flows locally? Ngrok? A dev Slack workspace? Anything documented?
- `npm run dev` — works? Brings up which surfaces? On which ports?
- Hello-world change: change a label, see it reflect. Documented?

Anything not documented is a finding.

## 2. The "deployment" path

Engineer A is given a small bug fix and asked to deploy.

- Branch from main? Push to PR? Vercel preview URL provisioned automatically?
- Tests run? On which surfaces?
- Pre-deploy gate (`quay-deploy-push-checklist`) applied?
- Promote to production: who, how, what approval?
- Rollback: how, by whom, in how long?
- If the deploy breaks n8n, who notices?
- Database migration: how is one written, tested, applied? Migration ordering?

## 3. The "operational" runbooks

For each common operational task, is there a runbook?

- Add a new founder mid-cohort.
- Remove a founder mid-cohort.
- Add a new mentor.
- Onboard a new staff member (provision Google Workspace, Slack, portal, Supabase, n8n access).
- Rotate a credential.
- Backfill a missed transcript.
- Handle a failed workflow execution.
- Re-send a magic link.
- Investigate a "founder says they didn't get the survey" report.
- Disaster recovery: Supabase project restored from backup, what else needs reconnecting?

## 4. The ownership map

For each surface and integration, who is the named owner?

- Slack app
- n8n workspace
- Supabase project
- Vercel project
- Google Workspace
- AI provider accounts
- Read.ai account
- The codebase as a whole
- Documentation

If the answer is "Ryan" for all of them, that's the bus factor.

## 5. The "where to edit what" map

A request like "the weekly survey copy should say X" — where does that change happen? The answer should be findable in ≤ 2 minutes by Engineer A. Audit a sample of common requests:

- Change a Slack message template.
- Change the proposal form fields.
- Change an AI prompt.
- Add a new metric to the staff dashboard.
- Change a Supabase RLS policy.

For each, document the file path. If no obvious answer exists, that's a finding.

# Severity System

- **P0** — Any of:
  - A routine operational task can only be done by Ryan (e.g., approving a new staff Vercel access, rotating a credential, restarting a stalled workflow).
  - No runbook exists for an incident that has happened more than once.
  - Production secrets are held only in Ryan's head / personal vault.
  - No one but Ryan can deploy.
  - No one but Ryan can administer a critical SaaS (Supabase, Vercel, n8n).
- **P1** — `.env.example` missing or incomplete. Local-dev setup not documented end-to-end. Migrations have no documented process. No ownership name on a critical surface.
- **P2** — Inline comments missing on non-obvious code. ADRs (architecture decision records) absent for major choices. Docs exist but are out of date.
- **P3** — Code style inconsistent. File-naming conventions drifted.

# Checklist

- [ ] Repo `README.md` exists, dated, with a clear "what is this" paragraph.
- [ ] `.env.example` complete; each variable has a one-line explanation and a "where to get this" pointer.
- [ ] Local-dev setup runs end-to-end on a clean machine; tested by a non-Ryan person if possible.
- [ ] Migration writing/applying procedure documented.
- [ ] Deployment process documented; rollback procedure documented.
- [ ] Runbooks exist for the operational tasks above.
- [ ] Each surface has a named human owner (even if all are Ryan today, name them so handoff knows what to reassign).
- [ ] Each SaaS dependency: account owner, billing owner, who has admin, MFA on all admins.
- [ ] ADRs for: why Supabase vs alternatives, why n8n vs alternatives, why Base44 vs scratch, why current AI providers.
- [ ] "Where to edit what" map exists or is implicit-and-trivial-to-find.
- [ ] Onboarding doc for a new staff engineer.
- [ ] Offboarding checklist for a departing staff engineer (rotates all credentials they touched).

# QUAY-Specific Questions

- If Ryan stopped touching the repo today, can another engineer:
  - Run it locally? — `npm install && npm run dev` and it works without IRL questions?
  - Deploy a bug fix? — through documented PR process?
  - Find the Slack signing secret if they need to rotate it?
  - Restart a stuck n8n workflow?
  - Add a new founder to an active cohort?
  - Find the Google service account JSON?
- The Base44 clone: is its origin documented? If the upstream changes, what's the merge story?
- The QUAY skills (`skills/quay/*`) — are they used during regular work, or are they shelfware that even Ryan forgot existed?
- Are there any "magic" steps Ryan does manually that aren't in any doc (e.g., "and then I open Sheets and copy the mentor list into Supabase")?

# Common Failure Modes

- **The undocumented magic step.** "Oh you also have to run this script after pulling new schema." Engineer A doesn't know; their local breaks; they think the project is broken.
- **The "Ryan knows" SaaS account.** Someone needs to add a Slack scope; only Ryan's account can; Ryan is on vacation; the team is blocked.
- **The README from three months ago.** Says to set `OPENAI_API_KEY`; the project moved to Anthropic; Engineer A spends an afternoon debugging.
- **The deploy that only works on Ryan's laptop.** A local-only env var, a manually-installed CLI, an SSH config — all of these are tribal knowledge.
- **The runbook that's a Notion link in a Slack DM.** Can't be found by anyone but the people in the DM.
- **The "we'll write docs when we have time."** Time never comes.

# Anti-Patterns

- "The code is self-documenting." It isn't for someone who didn't write it.
- Massive `README.md` no one reads. Better: short README with links to focused runbooks for specific tasks.
- Documenting how-to without why. "Run X" is useful; "Run X because the alternative Y has problem Z" is far more useful when X breaks.
- ADRs written and then never referenced.
- A `docs/` folder with files whose timestamps are all > 6 months old. Documentation that doesn't get updated *is* stale; treat it as suspect.

# Output Format

1. **Executive summary** — one paragraph: handoff readiness on a 1-5 scale; top 3 bus-factor risks.
2. **Handoff risk register** — the headline artifact. One row per risk: description, severity, who would be blocked, fix.
3. **Runbook gap list** — operational tasks with no runbook.
4. **Ownership map** — surface → owner. Gaps highlighted.
5. **Findings table** — concern, severity, fix.
6. **Severity** per rubric.
7. **Evidence** — missing files, missing sections, outdated dates, undocumented commands.
8. **Recommended fix** — write doc X; add runbook Y at path Z; assign owner W; rotate credential N out of Ryan's head into a managed store.
9. **Implementation complexity** — most fixes are `small` (write a doc) but require persistent attention. `medium` if a real handoff process needs to be designed.
10. **Owner/surface affected** — `handoff-maintainability`, `docs`, plus the affected surface.
11. **Follow-up questions** — who is the intended successor; what's the realistic timeline; should we hire / contract for handoff coverage.

# Example Prompt

> Audit QUAY for handoff readiness per `skills/quay/genius-team/handoff-maintainability-engineer/SKILL.md`. Walk the "first day," "deployment," and "operational runbook" paths from the perspective of an engineer who has never seen QUAY. Build the handoff risk register, runbook gap list, and ownership map. Emit findings per `FINDINGS_SCHEMA.md`. Do not modify code or docs. Append to current audit board.

# Related Skills

- [security-privacy-compliance-reviewer](../security-privacy-compliance-reviewer/SKILL.md) — credentials and rotation are core handoff items.
- [observability-telemetry-architect](../observability-telemetry-architect/SKILL.md) — runbooks are where alerts go.
- [n8n-workflow-reliability-engineer](../n8n-workflow-reliability-engineer/SKILL.md) — n8n workflows are the highest-handoff-friction surface.
- [product-scope-ruthless-prioritizer](../product-scope-ruthless-prioritizer/SKILL.md) — what stays, what goes, before handoff.
