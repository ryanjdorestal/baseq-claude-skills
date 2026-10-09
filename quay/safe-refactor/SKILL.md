---
name: quay-safe-refactor
description: Refactor QUAY code without breaking surfaces. A pre/post checklist for renames, extractions, type cleanups, and structural moves across the app, n8n, and Supabase.
---

# QUAY Safe Refactor Checklist

## Purpose

A refactor that changes behavior is a bug. This skill is the discipline for refactors that *preserve* behavior across QUAY's surfaces — Slack, n8n, Supabase, the Next.js portal, and AI callers. It exists because the platform's contracts cross multiple systems, and any rename or shape-change can ripple invisibly.

## When to use

- Renaming a column, function, route, event type, or schema field.
- Extracting a shared helper out of duplicated code.
- Replacing one library with another that "does the same thing."
- Restructuring directories.
- Cleaning up types that have drifted from runtime behavior.

Do **not** use it as cover for a behavior change. If the behavior changes, it's a feature/fix PR, not a refactor.

## Expected inputs

1. **The change** — exactly what is being renamed, moved, or restructured.
2. **Surfaces that depend on it** — app routes, n8n workflows, Slack handlers, AI prompts, Supabase RPCs, generated types.
3. **Compatibility window** — can we do an atomic rename, or do we need dual-write/dual-read?
4. **Test coverage** of the affected paths.

## Output format

A refactor PR includes:

1. **Behavior-preservation statement** in the PR body: "This PR does not change behavior. Evidence: [tests, screenshots, log diff]."
2. **Affected surfaces list** — every surface touched, with a one-line note.
3. **Before/after screenshots** for any user-visible code paths.
4. **Migration note** if Supabase or schemas changed.
5. **Test diff** — tests should not have to change their *expectations*; if they do, it's not a refactor.

## Rules

- **Atomic when small, staged when wide.** A rename touching < 5 call sites: one PR. A rename touching n8n + app + Supabase: stage as `add alias → migrate callers → remove original`, one PR each.
- **No "and while I was in there."** Unrelated cleanups go to their own PR.
- **Tests pin behavior before you refactor**, not after. If coverage is missing, add tests first as a separate PR.
- **Generated artifacts are regenerated** in the same PR (types, schemas, n8n exports). No "I'll regenerate later."
- **Search every surface.** A rename PR that only searches the app is incomplete — also search n8n workflow JSON, prompt files, doc files, and Supabase migrations.

## Constraints

- A refactor PR never touches `.env*`, secrets, or production config.
- A refactor PR never modifies n8n workflows in production directly — change is in git first, applied via the n8n CI step (or documented manual import).
- A refactor PR never bypasses [quay-ui-preservation](../ui-preservation/SKILL.md) — visually it must match.
- A refactor PR never lands without [quay-deploy-push-checklist](../deploy-push-checklist/SKILL.md) green on the resulting build.

## Anti-patterns

- "Refactor" PR that quietly changes a return type and breaks a downstream consumer.
- Renaming a Supabase column without a deprecation column + dual-write.
- Replacing a date library and "doing some formatting fixes too."
- Removing the only caller of a function and deleting the function in the same PR (delete in a follow-up so reverts are clean).
- Touching the Base44 baseline as a side-effect.

## Checklist

- [ ] Behavior-preservation statement written.
- [ ] Affected surfaces inventoried (app, n8n, Slack, AI, Supabase, schemas, types, docs).
- [ ] Searched every surface for the old name (grep + n8n JSON + prompt files).
- [ ] If wide-rippling: staged into `add alias → migrate → remove`.
- [ ] Tests pin behavior; no expectation changes in this PR.
- [ ] Generated types/schemas/exports regenerated and committed.
- [ ] Visual diff matches per [quay-ui-preservation](../ui-preservation/SKILL.md).
- [ ] No `.env*` or secret config touched.
- [ ] No unrelated cleanups in the diff.
- [ ] Deploy/push checklist passes on the resulting build.

## Example prompt

> I want to rename Supabase column `activity_events.actor_kind` to `activity_events.actor_type`. Use `skills/quay/safe-refactor/SKILL.md`. Produce the staged plan (alias → migrate → remove), the surfaces I need to search, the generated artifacts to regenerate, and the behavior-preservation statement. Do not make the change yet.
