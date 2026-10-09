---
name: quay-architecture-review
description: Audit the QUAY platform (or a branch of it) against its architectural spine — surface boundaries, data ownership, orchestration boundaries, and AI-feature placement — and emit a punch list.
---

# QUAY Platform Architecture Review

## Purpose

Produce a **single-screen health report** of the QUAY platform's architecture. Output is a punch list of drift between the current code and the spine described below. Every entry is fixable or explicitly waived.

This is not a linter. It looks for **structural** problems: surface coupling, data-ownership leaks, orchestration in the wrong place, AI calls in hot paths, and Base44-baseline drift.

## When to use

- Before merging any PR that adds a new surface (Slack command, portal route, n8n workflow).
- Before connecting a new system (Monday, a new AI provider, a new auth source).
- Before promoting a branch toward staging or prod.
- After any "ship it" sprint where speed beat discipline.

Do **not** use it as a pre-commit hook — it is a review tool, not a gate.

## Expected inputs

1. **Repo path** (default: cwd).
2. **Scope**: `all` | `slack` | `portal-internal` | `portal-client` | `n8n` | `supabase` | `ai`.
3. **Branch / PR reference** so findings can cite real lines.
4. **Optional waiver file** `.quay-audit-waivers.yaml` with `rule`, `path`, `reason`, `expires:` (required, ISO date).

## Output format

A markdown report at `./QUAY_ARCH_REVIEW.md`, sections in order:

1. **Summary line** — `N findings (X blocking, Y warning, Z info). Scope: <scope>.`
2. **Blocking findings** — must fix before merge. `rule · path:line · description · suggested fix`.
3. **Warnings** — should fix this sprint.
4. **Info** — opportunistic.
5. **Waived** — matched entries with expiry date.
6. **Surface map** — which surfaces exist, what data they read/write, where their logic lives.

Exit code: `0` if zero blocking, `1` otherwise.

## The QUAY spine (what the audit checks against)

- **One source of truth per entity.** Members, mentors, cohorts, activities live in Supabase. Slack, n8n, Monday, and Drive are surfaces or mirrors — never the master.
- **Surface code is thin.** Slack handlers, Next.js route handlers, and n8n nodes call into a shared domain layer; they do not embed business rules.
- **Orchestration lives in n8n only when it spans systems.** Single-system logic stays in the app. See [quay-n8n-boundaries](../n8n-boundaries/SKILL.md).
- **AI calls are explicit and bounded.** No silent model calls in request handlers. See [quay-ai-feature-implementation](../ai-feature-implementation/SKILL.md).
- **RLS is on for every table.** No table is unprotected, even "internal-only" ones. See [quay-supabase-schema](../supabase-schema/SKILL.md).
- **Base44 visual baseline is preserved.** UI changes go through [quay-ui-preservation](../ui-preservation/SKILL.md).
- **Schemas are the contract.** Anything crossing a process or system boundary (Slack event, n8n payload, AI tool call, webhook) has a typed schema.

## Constraints

- Read-only. Audit never writes app code, only `QUAY_ARCH_REVIEW.md`.
- Findings must cite `path:line`. No vague "somewhere in lib/".
- A finding without a **suggested fix** is not a finding.
- Waivers must have `expires:`. Expired waiver → blocking finding.

## Anti-patterns

- Slack handler reading Supabase via service-role key and bypassing RLS.
- A Next.js API route that calls Anthropic *and* writes Supabase *and* posts to Slack — that belongs in an n8n workflow or a queued job.
- Domain logic duplicated between an n8n node and an app route.
- AI prompt strings inline in a handler — they belong in a versioned prompt file.
- A new table without RLS, indexes, or a migration file.
- Visual change that "looks the same" but rewrites the underlying component tree — see [quay-ui-preservation](../ui-preservation/SKILL.md).

## Checklist

- [ ] Every surface is identified and mapped to its data and its orchestration owner.
- [ ] No domain logic in surface code (Slack handler, route handler, n8n custom function).
- [ ] No table without RLS.
- [ ] No AI call in a synchronous request path > 2s budget.
- [ ] No production secrets in `.env.example` or committed config.
- [ ] Every cross-system payload has a schema in `schemas/`.
- [ ] Base44 visual baseline preserved on every changed page (screenshot diff or explicit note).
- [ ] All findings cite `path:line` with a suggested fix.

## Example prompt

> Run a QUAY architecture review on the current branch, scope `all`. Cite findings against the spine in `skills/quay/architecture-review/SKILL.md`. Do not modify any app code. Write the report to `QUAY_ARCH_REVIEW.md` and summarize blockers in chat.
