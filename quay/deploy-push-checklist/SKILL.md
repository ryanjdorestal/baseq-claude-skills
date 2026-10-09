---
name: quay-deploy-push-checklist
description: The gate that runs before pushing to a shared branch or deploying QUAY to staging/production. Catches the predictable mistakes — secrets, migrations, env vars, broken surfaces — before they ship.
---

# QUAY Deploy / Push Checklist

## Purpose

A single, run-every-time gate before code leaves the developer's machine. The checklist is short on purpose: it catches the recurring mistakes (committed secrets, missing migration, env var not added in Vercel, n8n workflow drift) without trying to replace review.

## When to use

- Before `git push` to `main` or any shared branch.
- Before `vercel --prod`.
- Before importing an n8n workflow to the shared instance.
- Before applying a Supabase migration to staging or production.

Do **not** use it for local feature branches where you're still iterating — run it when you're about to share or ship.

## Expected inputs

1. **Branch** being pushed/deployed.
2. **Target** — `shared-branch`, `preview`, `staging`, `production`.
3. **Change summary** — one paragraph: what does this change do?
4. **Surfaces touched** — app, n8n, Supabase, prompts, schemas.

## Output format

Either:

- **Green:** a one-line confirmation per item, posted into the PR or deploy log.
- **Red:** the failing item and the exact fix.

For production, the result is committed to `DEPLOY_LOG.md` (or PR body) with timestamp and branch SHA.

## The gate

### Always

- [ ] `git status` clean — no uncommitted changes.
- [ ] No `.env*` file in the diff.
- [ ] No real secret (API key, service-role key, Slack token, n8n cred) in any file in the diff. Run a secret scan.
- [ ] `pnpm typecheck` passes.
- [ ] `pnpm lint` passes.
- [ ] `pnpm build` passes locally.
- [ ] All tests pass.

### If the app changed

- [ ] Vercel preview deploy reviewed in browser (internal + client surfaces).
- [ ] Base44 baseline preserved per [quay-ui-preservation](../ui-preservation/SKILL.md).
- [ ] No new env var without an entry in `.env.example` *and* a value set in Vercel (Development + Preview + Production).

### If Supabase changed

- [ ] Migration file present in `supabase/migrations/`.
- [ ] `supabase db reset` runs clean locally.
- [ ] RLS policies present on every new table.
- [ ] Generated types regenerated and committed.
- [ ] For destructive changes: dual-write / deprecation window documented.

### If n8n changed

- [ ] Workflow JSON exported and committed to the repo's workflow directory.
- [ ] Schemas for new webhooks committed.
- [ ] No credential strings in the exported JSON — only credential references.
- [ ] Idempotency key handling verified.

### If AI changed

- [ ] Prompt file versioned per [quay-ai-feature-implementation](../ai-feature-implementation/SKILL.md).
- [ ] Eval cases run; regressions documented or fixed.
- [ ] No prompt or model key reachable from the browser.

### Production-only extras

- [ ] Change reviewed and approved by at least one other person.
- [ ] On-call notified if this is a high-blast-radius change.
- [ ] Rollback plan written: "If this breaks, we revert commit `<sha>` and redeploy."
- [ ] Deploy window respected (no production deploys late Friday unless it's a hotfix).

## Constraints

- The checklist is the floor, not the ceiling. It does not replace review.
- A red item is a hard stop. No "we'll fix it after."
- No `git push --force` to `main` or any shared branch.
- No bypassing pre-commit / pre-push hooks (`--no-verify` is forbidden unless the user explicitly authorizes it for a specific known-good reason).
- Never deploy from a dirty tree or from someone else's machine.

## Anti-patterns

- Running the checklist *after* deploying "to save time."
- Treating green-on-local as proof it'll work on Vercel — env parity matters; verify Preview first.
- Skipping the n8n export because "the change is small."
- Migration that "just adds a nullable column" still skips RLS check.
- A rollback plan that says "we'll figure it out."

## Checklist (the short version, for muscle memory)

- [ ] Clean tree, no secrets, no `.env*` in diff.
- [ ] Typecheck + lint + build + tests green.
- [ ] If app: preview reviewed, visual baseline preserved, env vars in Vercel.
- [ ] If Supabase: migration + RLS + types regenerated.
- [ ] If n8n: workflow JSON committed, schemas committed.
- [ ] If AI: prompt versioned, evals run.
- [ ] If prod: review, on-call, rollback plan, deploy window.

## Example prompt

> Run the deploy/push checklist per `skills/quay/deploy-push-checklist/SKILL.md` against this branch. Target: production. Tell me each item's status. Do not push or deploy. Stop at the first red and tell me the fix.
