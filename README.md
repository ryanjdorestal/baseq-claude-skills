# BaseQ Claude Skills

Claude skills I wrote while building the first version of Quay's platform (QUAY OS), shared with the BaseQ team so you can move faster with Claude Code or any agent that reads Markdown instructions.

These are prompts and checklists, not code you import. Each one tells Claude how to approach a specific kind of task (designing a Supabase table, deciding what belongs in n8n, reviewing scope, auditing auth) so you get consistent, reviewable output instead of starting every prompt from scratch.

## What's inside

**`quay/`: 12 task skills for the platform**

| Skill | Use it when |
|---|---|
| `supabase-schema` | Designing or changing a table, its RLS policies and migration |
| `mentor-crm-model` | Working on mentors, expertise, availability and intros |
| `client-portal` | Building founder-facing screens |
| `internal-dashboard` | Building staff/admin screens |
| `activity-feed-model` | Combining events from Slack, Read.ai, Drive into one feed |
| `ai-feature-implementation` | Adding any AI feature (model choice, prompts, cost, evaluation) |
| `n8n-boundaries` | Deciding what runs in n8n vs. in the app |
| `architecture-review` | Checking a branch against the overall design |
| `safe-refactor` | Renaming or restructuring without breaking screens |
| `ui-preservation` | Changing visuals without losing the agreed baseline |
| `deploy-push-checklist` | Before merging to main or deploying |
| `vercel-nextjs-execution` | Deploying on Vercel (written for Next.js; the env var and preview-deploy parts apply to Vite too) |

**`quay/genius-team/`: a senior review panel**

Sixteen reviewer skills (scope prioritizer, auth architect, multi-tenant boundaries, AI cost, QA scenarios, handoff readiness and more) plus an orchestrator. Start with `quay/genius-team/README.md`. The **product-scope-ruthless-prioritizer** and **handoff-maintainability-engineer** are the two most useful for an 8-week term.

**`tribunal/`: adversarial review**

A system that attacks a piece of work with hostile reviewers, then attacks its own reviewers so it doesn't hand you made-up problems. It was built for research papers, but the idea carries over to reviewing a PRD, a design doc or a matching evaluation. Start with `tribunal/README.md`.

## How to use them with Claude Code

1. Copy the folders you want into your repo under `.claude/skills/` (or `~/.claude/skills/` to use them across projects).
2. Claude Code picks up any folder with a `SKILL.md` and uses it when the task matches its description. You can also point Claude at a file directly: "Follow `.claude/skills/supabase-schema/SKILL.md` for this migration."
3. Edit freely. These were written for my build (plain JS, Base44 clone, Slack bot, n8n). Where they mention my stack, swap in yours.

## Notes

- Written in spring 2026 for QUAY OS. Some references (Slack bot, n8n, Monday) describe systems that may no longer be in use.
- No keys, credentials or client data are in this repo.
- I'm not maintaining this. Fork it and make it yours.

Ryan Dorestal
