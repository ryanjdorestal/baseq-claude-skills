# QUAY Skills Catalog

Reusable skill docs for building the **QUAY** AI-native accelerator operating platform.

## What QUAY is

A multi-surface platform that runs day-to-day accelerator operations and member experience:

- **Slack bot runtime** — primary surface for staff + members
- **n8n orchestration** — workflow glue between systems
- **Google Drive document flows** — source-of-truth for docs/contracts/intake
- **Read.ai transcript ingestion** — meeting capture → activity feed + AI summaries
- **Monday sync (planned)** — task + roadmap mirror
- **Supabase backend (planned)** — primary data store, auth, RLS
- **Vercel-hosted platform (planned)** — Next.js app; internal + client surfaces
- **Base44 app (cloned)** — visual baseline already in place and usable

Two human surfaces:

1. **Internal employee platform** — staff, ops, mentor coordinators
2. **Client / founder-facing platform** — accelerator members

## How to use these skills

Each `skills/quay/<name>/SKILL.md` is a self-contained doc with the same nine sections:

1. Purpose
2. When to use
3. Expected inputs
4. Output format
5. Constraints
6. Anti-patterns
7. Checklist
8. Example prompt
9. (frontmatter at top with `name` + `description`)

Pull a skill into a working session by either pointing Claude at the file or copying the relevant checklist into the prompt.

## Skills

| Skill | Purpose |
|---|---|
| [quay-architecture-review](./architecture-review/SKILL.md) | Audit the platform against its architectural spine |
| [quay-supabase-schema](./supabase-schema/SKILL.md) | Design or evolve Supabase tables + RLS |
| [quay-vercel-nextjs-execution](./vercel-nextjs-execution/SKILL.md) | Run, build, and deploy the Next.js app safely |
| [quay-ui-preservation](./ui-preservation/SKILL.md) | Preserve the Base44 visual baseline while upgrading |
| [quay-internal-dashboard](./internal-dashboard/SKILL.md) | Design the internal employee dashboard |
| [quay-client-portal](./client-portal/SKILL.md) | Design the client/founder-facing portal |
| [quay-mentor-crm-model](./mentor-crm-model/SKILL.md) | Model the mentor network as a CRM |
| [quay-activity-feed-model](./activity-feed-model/SKILL.md) | Model the unified event/activity feed |
| [quay-n8n-boundaries](./n8n-boundaries/SKILL.md) | Decide what lives in n8n vs. the app |
| [quay-ai-feature-implementation](./ai-feature-implementation/SKILL.md) | Add AI features safely (Anthropic SDK) |
| [quay-safe-refactor](./safe-refactor/SKILL.md) | Refactor without breaking surfaces |
| [quay-deploy-push-checklist](./deploy-push-checklist/SKILL.md) | Pre-push and pre-deploy gates |

## Hard rules

- **Do not modify production app code** from skill-prep sessions.
- **Do not touch secrets** — `.env*`, Supabase service-role keys, Slack tokens, n8n credentials, AI provider keys.
- **Do not deploy or push** from a skill-prep session.
- The Base44 visual baseline is the **default UI contract**. Visual upgrades are deliberate, not incidental.
- The schema is the contract between Supabase, n8n, Slack, and the Next.js app. No "just pass a dict."

## QUAY vocabulary

Use these terms consistently across skills, code, and docs:

- **member** — accelerator participant / founder (not "user", not "customer")
- **mentor** — external advisor in the network
- **cohort** — a time-boxed group of members
- **staff** — internal employees
- **activity** — a recorded event (meeting, doc edit, intro, milestone)
- **workflow** — an n8n orchestration
- **surface** — a place a human interacts (Slack, web portal, email)
- **portal** — the web app surface (internal or client)
