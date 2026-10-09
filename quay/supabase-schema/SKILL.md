---
name: quay-supabase-schema
description: Design or evolve a Supabase table — columns, indexes, RLS policies, migrations, and TypeScript types — for the QUAY platform. Schema is the contract.
---

# QUAY Supabase Schema Design

## Purpose

Own the lifecycle of a Supabase table in QUAY: create new tables, evolve existing ones, generate RLS, indexes, and types so the schema stays the single source of truth across Slack, n8n, the Next.js portal, and AI features.

Every table has: a migration file, RLS policies, indexes for known access patterns, generated TypeScript types, and at least one seed row for local dev.

## When to use

- Adding a new entity (cohort, mentor session, intro, doc, milestone).
- Evolving an existing entity (new column, new enum value, new relationship).
- Discovering an undocumented table or column and bringing it under control.
- Before any feature that reads or writes Supabase from a new surface.

Do **not** use it for purely in-memory or cache data — that does not need a Supabase table.

## Expected inputs

1. **Entity name** in `snake_case`, plural (e.g. `mentor_sessions`, `activity_events`).
2. **Owner** — which surface or workflow is the primary writer (`portal-internal`, `portal-client`, `n8n`, `slack`).
3. **Columns** — name, Postgres type, nullable, default, unit/enum, description.
4. **Relationships** — FKs and the cascade behavior.
5. **Access patterns** — who reads, who writes, with which filters (drives indexes + RLS).
6. **Sensitivity** — `public`, `member-scoped`, `staff-only`, `secret`.

## Output format

Files written, in order:

1. **`supabase/migrations/<timestamp>__<entity>.sql`** — `CREATE TABLE`, indexes, FKs, `ALTER TABLE … ENABLE ROW LEVEL SECURITY`, and explicit `CREATE POLICY` statements.
2. **`supabase/seed/<entity>.sql`** — at least one realistic seed row.
3. **`types/database.ts` (or generated equivalent)** — regenerated with `supabase gen types typescript`.
4. **`docs/data-model/<entity>.md`** — one-pager: purpose, owner, columns, RLS summary, access patterns, related entities.
5. **`schemas/<entity>.ts`** — Zod schema mirroring the row shape for runtime validation at API boundaries.

## RLS rules (defaults)

- **Default deny.** `ENABLE ROW LEVEL SECURITY` on every table at creation time, never later.
- **Staff role:** read/write where `auth.jwt() ->> 'role' = 'staff'`.
- **Member role:** read where `member_id = auth.uid()` or via membership in the row's cohort. Write only on tables the member legitimately owns (their own profile, their own submissions).
- **Service role** bypasses RLS — only n8n and trusted server-side jobs use it, never the browser.
- Every policy is named: `<table>_<role>_<verb>` (e.g. `mentor_sessions_member_select`).

## Naming + structure conventions

- Table names: `snake_case`, plural.
- Primary key: `id uuid default gen_random_uuid()`.
- Timestamps: `created_at timestamptz not null default now()`, `updated_at timestamptz not null default now()` with a trigger.
- Soft delete: `deleted_at timestamptz` only when truly needed; otherwise hard-delete.
- Enums: Postgres `CREATE TYPE … AS ENUM`, lowercase values, no spaces.
- FKs: `<entity>_id`, `on delete` is **explicit** (`cascade`, `restrict`, or `set null` — never default).
- Indexes: every FK indexed, plus one for each documented filter access pattern.

## Constraints

- No table without RLS.
- No migration that drops a column without a deprecation step + at least one release of dual-write.
- No `select *` policies for the member role — list columns explicitly when sensitive data exists.
- No business logic in triggers beyond `updated_at` maintenance or referential housekeeping.
- Service-role key never appears in client-side code or in a Slack bot bundle.

## Anti-patterns

- A "users" table — QUAY has `members`, `mentors`, and `staff`, distinct entities even if backed by `auth.users`.
- Storing Slack/Drive/Monday IDs in ad-hoc string columns with no constraint or index.
- Putting AI-generated content in the same row as the source — split into `<entity>` and `<entity>_summaries`.
- Reusing one giant `metadata jsonb` column instead of typed columns when the shape is known.
- A new column without a default that breaks existing rows.

## Checklist

- [ ] Migration file named `<timestamp>__<entity>.sql`, present in `supabase/migrations/`.
- [ ] `ENABLE ROW LEVEL SECURITY` plus explicit policies.
- [ ] Every FK has an index.
- [ ] `created_at`, `updated_at` present; `updated_at` trigger wired.
- [ ] Generated types regenerated and committed.
- [ ] Zod schema in `schemas/` mirrors row shape.
- [ ] `docs/data-model/<entity>.md` written.
- [ ] At least one seed row.
- [ ] Local migration runs clean (`supabase db reset`) before pushing.

## Example prompt

> Design a Supabase table for `mentor_sessions` per `skills/quay/supabase-schema/SKILL.md`. Columns: id, mentor_id, member_id, scheduled_at, duration_minutes, status enum (scheduled|completed|no_show|cancelled), notes_doc_id, source enum (manual|read_ai|calendar). RLS: staff full, mentor sees own, member sees own. Emit the migration, types, schema, seed, and doc.
