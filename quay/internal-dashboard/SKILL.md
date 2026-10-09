---
name: quay-internal-dashboard
description: Design and build the internal employee dashboard for QUAY — what staff see, what they act on, and how to keep it fast and noise-free.
---

# QUAY Internal Employee Dashboard Design

## Purpose

Define the design and implementation contract for the **staff-facing** portal: cohort coordinators, ops, and mentor managers. The dashboard is an *action surface*, not a reporting surface. Every block on the page either tells a staff member to do something or shows the state of something they own.

## When to use

- Adding a new staff-only page, widget, or workflow surface.
- Reviewing a proposed dashboard layout or AI-suggested staff feature.
- Cutting noise from an existing dashboard that has drifted into a wall of charts.
- Wiring a new data source (Read.ai, Monday, Drive) into the staff view.

Do **not** use it for member-facing surfaces — see [quay-client-portal](../client-portal/SKILL.md).

## Expected inputs

1. **Staff role** — `coordinator`, `ops`, `mentor_manager`, `admin`.
2. **Time horizon** — what window of activity matters (today, this week, this cohort).
3. **Action types available** — what the staff member can do from the page (intro a mentor, flag a member, mark complete).
4. **Data sources** — Supabase tables, n8n-derived views, AI summaries.

## Output format

For a new or redesigned dashboard page:

1. **Wireframe note** — block-by-block list: title, data source, action, refresh cadence.
2. **Route + component layout** — Next.js route, server vs. client components, loading + error boundaries.
3. **Supabase queries** — exact `select` shapes with explicit columns and indexes used.
4. **RLS check** — the policy the staff role relies on (named, per [quay-supabase-schema](../supabase-schema/SKILL.md)).
5. **Empty state** — what the page looks like when nothing is happening.
6. **Performance budget** — target TTFB and the largest query.

## Core blocks (default staff dashboard)

1. **Today's actions** — a list of things only a human can do (introductions to make, sessions to confirm, members to check on). Source: activity feed + open tasks.
2. **At-risk members** — surfaced by rule + AI signal (missed sessions, dropped engagement). Each entry has a one-click action.
3. **Mentor capacity** — who has open slots this week, who is overbooked. Source: mentor CRM.
4. **Recent activity** — last 24h across surfaces (Slack, Read.ai, Drive). Compressed to one line per event.
5. **Pinned cohort context** — current cohort's stage, key dates, blockers.

Anything not in these five categories needs a justification.

## Constraints

- Staff dashboard is **read-mostly, action-precise**. No multi-step forms on the dashboard; deep-link to the action surface.
- Each block has a single owner (a Supabase view or a named query), a refresh cadence, and a defined empty state.
- AI-generated summaries are clearly labeled and timestamped. Never inline AI text as if it were human-written.
- Page must render usable content in < 1s p95 with no AI-blocking call in the critical path.
- All blocks respect RLS — no bypassing via service role from the browser.

## Anti-patterns

- A page full of charts with no actions.
- "Activity log" that dumps every event — see [quay-activity-feed-model](../activity-feed-model/SKILL.md) for compression rules.
- A widget that requires a fresh AI call on every render.
- Staff-only data leaking into member-visible API responses because the same endpoint serves both.
- Mixing cohort-scoped and global data in one block without a clear filter.

## Checklist

- [ ] Each block: title, data source, action, refresh cadence documented.
- [ ] Empty state defined for each block.
- [ ] Supabase queries listed with the index they use.
- [ ] RLS policy named and verified for the staff role.
- [ ] No AI call in the critical render path; AI summaries are pre-computed and stored.
- [ ] At least one action is one click away from every block.
- [ ] Page meets the perf budget on a cold cache.
- [ ] Screenshots match Base44 baseline per [quay-ui-preservation](../ui-preservation/SKILL.md).

## Example prompt

> Design the v1 internal dashboard for the `coordinator` role per `skills/quay/internal-dashboard/SKILL.md`. Use the five default blocks. Output wireframe note, route + component layout, Supabase queries with index usage, RLS policy names, and empty states. Do not write app code — produce the design doc only.
