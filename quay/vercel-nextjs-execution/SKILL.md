---
name: quay-vercel-nextjs-execution
description: Run, build, preview, and deploy the QUAY Next.js app on Vercel safely. Covers env vars, build commands, preview deploys, and the pre-prod gate.
---

# QUAY Vercel / Next.js Execution

## Purpose

A single procedure for running the QUAY Next.js app locally, getting a Vercel preview, and producing a production deploy without surprises. Treats deploy as a deliberate, reviewable act — never a side-effect of saving a file.

## When to use

- First-time setup on a new machine.
- Verifying a branch in a Vercel preview before review.
- Promoting a reviewed branch to production.
- Diagnosing a build that works locally but fails on Vercel (or vice versa).

Do **not** use it for hotfixes that bypass review — escalate instead.

## Expected inputs

1. **Repo path** to the Next.js app.
2. **Target environment** — `local` | `preview` | `production`.
3. **Branch** — for preview/prod deploys.
4. **`.env.local`** populated from the team password manager. Never commit it.

## Output format

For each invocation, log to chat (or `DEPLOY_LOG.md` if requested):

- Resolved Node + pnpm/npm version.
- Build command + output summary (warnings, bundle size, route count).
- For preview/prod: Vercel deployment URL and inspect URL.
- For prod: the gate result (see [quay-deploy-push-checklist](../deploy-push-checklist/SKILL.md)).

## Standard commands

```bash
# Local dev
pnpm install
pnpm dev               # http://localhost:3000

# Type + lint + build (the local prod gate)
pnpm typecheck
pnpm lint
pnpm build

# Vercel preview (from a branch)
vercel                 # interactive first time; then non-interactive
vercel --prebuilt      # if local build already succeeded

# Vercel production
vercel --prod          # only after deploy-push-checklist passes
```

If commands differ in the repo, prefer the repo's `package.json` scripts and document them here.

## Env var conventions

- `NEXT_PUBLIC_*` only for values safe to ship to the browser (URLs, public Supabase anon key, feature flags). Everything else is server-only.
- Three environments in Vercel: **Development**, **Preview**, **Production**. Every required var must be set in all three or the build fails loudly — never with a silent default.
- Secrets (Supabase service-role, Slack bot token, Anthropic API key, n8n webhook signing keys) live only in Vercel env + the password manager. Never in `.env.example` with a real value.
- `.env.example` lists every required var with a placeholder and a one-line description.

## Constraints

- Never run `vercel --prod` without the deploy/push checklist green.
- Never deploy from a dirty working tree. Commit, push, then deploy from a clean ref.
- Never bypass the type check or lint to ship.
- Never paste a secret into chat, logs, or screenshots.
- Production builds are reproducible: lockfile committed, Node version pinned (`.nvmrc` or `engines`).

## Anti-patterns

- Editing env vars directly in Vercel UI without mirroring the change in `.env.example` and the password manager.
- Using `vercel link` against the wrong project (e.g. linking a fork to the prod project).
- Adding `// @ts-ignore` to make a build pass — fix the type or the call site.
- Running `pnpm build` with `NODE_ENV=development` and assuming it represents prod.
- Skipping a preview deploy because "it's a small change."

## Checklist

- [ ] `pnpm install` clean against the committed lockfile.
- [ ] `pnpm typecheck` passes.
- [ ] `pnpm lint` passes.
- [ ] `pnpm build` passes locally.
- [ ] Preview deploy URL reviewed in browser, both internal and client surfaces.
- [ ] No new env var without `.env.example` + password-manager entry.
- [ ] Bundle size and route count are not surprising (note any new heavy dep).
- [ ] Deploy-push checklist run before `--prod`.

## Example prompt

> Walk me through producing a Vercel preview deploy for branch `feature/mentor-portal-v2` per `skills/quay/vercel-nextjs-execution/SKILL.md`. Do not deploy to production. Stop before any destructive action and confirm with me.
