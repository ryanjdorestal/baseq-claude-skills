---
name: quay-mentor-crm-model
description: Model the QUAY mentor network as a CRM — mentors, their expertise, their availability, their relationships, and their interactions with members. Defines the canonical schema and access patterns.
---

# QUAY Mentor Network / CRM Modeling

## Purpose

Treat mentors as a first-class entity, not a side-effect of sessions. This skill defines the canonical mentor data model and the access patterns that depend on it: matching members to mentors, tracking capacity, recording outcomes, and respecting privacy.

## When to use

- Onboarding the mentor network into Supabase for the first time.
- Adding a mentor attribute (skill, region, language, capacity rule).
- Building a mentor-matching feature, a capacity dashboard, or a mentor newsletter.
- Migrating mentor data from a spreadsheet, Monday, or HubSpot.

Do **not** use it for member-only relationships — members are not modeled here. See [quay-supabase-schema](../supabase-schema/SKILL.md).

## Expected inputs

1. **Source of truth** for mentor records (spreadsheet, Monday, HubSpot, manual entry).
2. **Required attributes** for matching (expertise areas, region, stage focus, languages).
3. **Capacity rules** (sessions per month, blackout dates, paused status).
4. **Privacy rules** — what members can see about a mentor, what they cannot.

## Canonical entities

- **`mentors`** — identity, contact, status (`active`, `paused`, `archived`), join date, owner staff member.
- **`mentor_expertise`** — many-to-many with a controlled-vocabulary `expertise_tags` table.
- **`mentor_availability`** — recurring rules + ad-hoc windows.
- **`mentor_sessions`** — every session with a member; links to `activity_events`.
- **`mentor_notes`** — staff-only notes about a mentor. Never member-visible.
- **`mentor_relationships`** — long-running pairings between a mentor and a member (a mentor may have several).
- **`mentor_feedback`** — post-session feedback, both directions; member-visible fields are explicitly scoped.

## Output format

For a new feature against the mentor model:

1. **Entity diagram** — boxes + lines for the entities involved.
2. **Migration files** — per [quay-supabase-schema](../supabase-schema/SKILL.md).
3. **RLS policies** — staff full, mentor sees own records, member sees only fields explicitly marked member-visible.
4. **Query catalog** — the named queries the app/n8n calls (e.g. `mentors_with_open_capacity_for_tag`, `mentor_session_history_for_member`).
5. **Sync notes** — if Monday or HubSpot is the source, how the sync runs, conflict rules, idempotency keys.

## Matching contract

A mentor-matching query returns candidates ordered by:

1. Availability in the requested window (hard filter).
2. Expertise overlap with the member's current need (scored).
3. Existing relationship with the member (bonus, not a hard requirement).
4. Recent session load (de-prioritize over-utilized mentors).

The query is named, indexed, and tested. AI assistance can re-rank but cannot bypass these filters.

## Constraints

- **Mentor notes are staff-only.** No surface ever returns `mentor_notes` to a member.
- **Status changes are auditable** — a mentor going from `active` to `paused` writes an `activity_event`.
- **Idempotent sync.** If Monday or HubSpot is the source, syncs are keyed by a stable external id and write deltas only.
- **No silent capacity overrides.** A staff member can override capacity, but the override is recorded with a reason.
- **PII boundaries** — mentor personal email, phone, address are masked in any member-visible response.

## Anti-patterns

- One giant `mentors` table with a `notes` text field used as a junk drawer.
- Treating expertise as a freeform comma-separated string instead of a tag table.
- Hardcoding "top mentors" outside the matching query.
- Sending member-identifying data to a mentor before the member has opted in.
- Letting AI summaries persist on the mentor row without a reference back to the source sessions.

## Checklist

- [ ] Canonical entities present (or explicitly scoped down for v1).
- [ ] Tag tables exist for expertise; no freeform expertise columns.
- [ ] Mentor notes table is staff-only with a named RLS policy.
- [ ] Matching query is named, indexed, and documented.
- [ ] Status change → activity_event row is wired.
- [ ] If syncing from Monday/HubSpot: idempotency key + conflict rule documented.
- [ ] No PII in member-visible response shapes.
- [ ] Capacity overrides require a reason.

## Example prompt

> Model the v1 mentor CRM per `skills/quay/mentor-crm-model/SKILL.md` against current Supabase tables. Source of truth: existing spreadsheet (path provided). Required attributes: expertise tags, region, stage focus, capacity per month. Produce entity diagram, migration plan, RLS policies, and the matching query. Do not write app code — design doc only.
