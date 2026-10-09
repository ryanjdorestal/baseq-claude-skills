---
name: quay-client-portal
description: Design and build the founder/member-facing portal for QUAY — what members see, what they can do, and how to keep the surface focused and trustworthy.
---

# QUAY Client / Founder Portal Design

## Purpose

Define the design contract for the **member-facing** portal: founders going through a QUAY cohort. The portal exists to (1) show the member where they are in the program, (2) give them one-click access to the next thing they need, and (3) surface the human relationships (mentors, staff) on their side.

It is not a reporting tool, not a CRM, and not a chat client.

## When to use

- Adding a new member-facing page or component.
- Reviewing a proposed member feature or AI-suggested member-side surface.
- Cutting noise from an existing member view.
- Wiring member-facing notifications across Slack + email + portal.

Do **not** use it for staff surfaces — see [quay-internal-dashboard](../internal-dashboard/SKILL.md).

## Expected inputs

1. **Cohort stage** — what part of the program the member is in.
2. **Available actions** — what a member can do right now (book mentor, submit doc, RSVP).
3. **Data sources** — Supabase rows scoped to this member; AI summaries pre-computed.
4. **Notification channels** the surface needs to coordinate with.

## Output format

For a new or redesigned member page:

1. **Page outline** — hero + 3-5 content blocks max. Each block: title, data, action.
2. **Route + component layout** — Next.js route, auth gate, RLS-scoped queries.
3. **Supabase queries** — `select` shapes, RLS policy used.
4. **Empty state** — what a brand-new member sees on day one.
5. **Notification mapping** — which on-page events trigger Slack/email/in-app.
6. **Mobile layout** — explicit, not "responsive by accident."

## Core blocks (default member portal home)

1. **Your next step** — one card, one action. The single most important thing this member can do today.
2. **Your mentors** — who they are, when the next session is, one-click to schedule.
3. **Your cohort** — current stage, key dates, peer activity (compressed).
4. **Your documents** — Drive-linked artifacts the member owns or needs to review.
5. **Get help** — escalation path (Slack channel, staff contact) — always visible, never hidden in a menu.

Anything beyond these five needs a justification and should probably be a separate page.

## Constraints

- Member portal is **focused and respectful**: one primary action per page, no infinite scroll.
- RLS is enforced — a member must never be able to query another member's data even if they craft the request.
- AI-generated content is labeled and dated; the source link is always available.
- No staff-only data leaks into a member-visible endpoint, ever.
- Notifications follow a single rule: one event → one channel by default. Cross-posting is opt-in.
- Loading and error states are designed, not default browser behavior.

## Anti-patterns

- A "for you" feed of mixed updates that's hard to scan or act on.
- Showing internal status fields (e.g. "flagged as at-risk") to the member.
- AI summary of the member's own data presented as if it were a coach speaking.
- Asking the member to do something the system could have done for them.
- Hiding the help/escalation path behind a profile menu.

## Checklist

- [ ] One primary action per page identified.
- [ ] All queries RLS-scoped to the authenticated member.
- [ ] No staff-only fields exposed in the response shape.
- [ ] Empty state defined for first-day-of-cohort experience.
- [ ] Mobile layout reviewed at 375px.
- [ ] Notification mapping documented (no surprise cross-posts).
- [ ] AI content labeled and dated.
- [ ] Visual diff matches Base44 baseline per [quay-ui-preservation](../ui-preservation/SKILL.md).
- [ ] Help / escalation path visible on every page.

## Example prompt

> Design the v1 member portal home per `skills/quay/client-portal/SKILL.md` for a member in the "build phase" of a cohort. Use the five default blocks. Output page outline, route, queries with RLS policies, empty state, and mobile layout. Do not write app code — design doc only.
