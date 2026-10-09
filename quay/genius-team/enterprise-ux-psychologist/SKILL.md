---
name: quay-enterprise-ux-psychologist
description: Reviews QUAY's user experience for trust, clarity under stress, decision support, and recoverability. Tests whether the UI helps founders, mentors, and staff make the right call quickly — or whether it looks pretty while hiding ambiguity.
---

# Purpose

Institutional users (founders deciding whether to act on a proposal, staff coordinating across 30 founders, mentors deciding whether to take an intro) need the UI to reduce uncertainty under cognitive load. QUAY's current UI inherits Base44's polish but has not been pressure-tested as an *operational* tool. A pretty empty state isn't useful at 11pm when a founder is trying to figure out whether their proposal got rejected.

This skill audits the UX of every surface from the **user's worst moment**, not their best. It catches dashboards that exist for show, status fields that look authoritative but mean nothing, AI-generated content presented as fact, and approval flows that confuse rather than confirm.

# When to Use

- Every full audit.
- Before exposing a surface to external users (founders directly, clients directly, mentors directly).
- When users (founders, mentors) report confusion or "I didn't know what to do."
- After an `institutional-pm-reviewer` finding that a feature is "operational" — this skill checks whether the operational experience is actually usable.
- During UX-focused rebuilds or migrations away from Base44 visuals.

# Expected Inputs

1. The list of user-facing screens by role.
2. The current copy on key screens (headings, status labels, button text, empty states, error messages).
3. Sample data states (loading, empty, error, partial, complete).
4. AI artifacts and where they appear in the UI.

# Required Context to Inspect

- `portal-client/` and `portal-internal/` routes.
- Slack bot message templates (the bot is a UI too).
- Email templates if any (transactional emails are a UI).
- Status labels in the schema (these often leak into UI verbatim — bad).

# Review Methodology

For each screen / message / artifact, run the **trust & clarity audit**:

## 1. What is the user trying to decide here?

If you can't answer in one sentence, the screen is poorly scoped. (Hand off to `institutional-pm-reviewer` if the *feature* itself lacks purpose; this skill assumes the feature has a purpose and asks whether the UI supports it.)

## 2. Where is the eye supposed to go first?

Identify the **primary action** — the single most important thing on the screen. If there isn't one, the screen has no point of view. If there are three things competing for primary, the user pays attention to none.

## 3. What happens at the worst moment?

For each screen, walk through:
- **Loading** — does the user see a spinner forever, or a meaningful skeleton with the data shape implied?
- **Empty** — is "you have nothing yet" framed as an opportunity ("invite a mentor") or as a void ("no data")?
- **Partial** — half the data loaded, half didn't. Is the user told, or are they shown half-state silently?
- **Error** — is the message diagnostic ("the transcript couldn't be loaded; try refresh; contact staff if this persists") or terrifying ("Error: ENOENT")?
- **Stale** — data was last updated 2 hours ago. Does the user know?

## 4. Trust audit for AI surfaces

For every AI-generated artifact (proposal draft, transcript summary, intelligence note):
- Is it **labeled** as AI-generated, or does it appear as if a human wrote it?
- Is there a clear path to **edit or override** it?
- Does it cite sources, or assert facts unsupported?
- What does the user think when the AI is wrong? (If "they trust it anyway," the trust gradient is broken.)

## 5. Approval & destructive actions

- Is there a confirmation before destructive actions (delete, archive, remove from cohort)?
- Are approvals (proposal approve, intro confirm) **reversible** within a window? If not, are they preceded by adequate context?
- After action, does the UI confirm what happened with specifics ("Proposal #42 approved; founder notified via Slack at 14:32") or vaguely ("Done")?

## 6. The founder vs staff vs mentor lens

- A **founder** is often emotional (this is their company). UI should be calm, supportive, predictable. No surprises, especially not about their status.
- A **staff** member is task-loaded (managing 30+ founders, multiple cohorts). UI should be dense, prioritized, scannable. Surface the few things needing decision; hide everything else.
- A **mentor** is in volunteer mode (helping when they can). UI should be minimal, clear-on-skim, easy to leave and return to.

Same data, different surface treatment. A single shared dashboard is almost always wrong.

# Severity System

- **P0** — Any of:
  - UI makes a founder believe a decision was made when it wasn't, or vice versa.
  - AI-generated content presented as a staff-authored decision/communication, with no label.
  - A destructive action with no confirmation and no rollback.
  - Status displayed authoritatively but derived from stale/missing data ("you're on track" while ingestion is broken).
- **P1** — Empty states that confuse ("no data" when the user expects something specific). Error states that surface raw exceptions. Loading states that block useful interaction. AI artifacts editable in theory but with no obvious affordance.
- **P2** — Two pages doing the same job slightly differently. Status labels inconsistent ("submitted" on one page, "pending" on another). Mentor and founder views show the same dashboard.
- **P3** — Visual polish gaps; typography drift; copy that's correct but cold.

# Checklist

For each screen / surface:

- [ ] Primary user role declared.
- [ ] Primary action identified.
- [ ] Loading state designed.
- [ ] Empty state designed and framed positively.
- [ ] Partial-data state handled or explicitly impossible.
- [ ] Error state diagnostic and actionable.
- [ ] Stale-data indicator present where applicable.
- [ ] AI content labeled and editable.
- [ ] Destructive actions confirmed.
- [ ] Approvals confirmed with specifics.
- [ ] Confidence in status labels: each label means one specific thing; users have been told.
- [ ] Same surface not trying to serve two roles with conflicting needs.
- [ ] Copy uses QUAY vocabulary consistently (member, mentor, cohort, staff, activity).

For approval flows specifically:

- [ ] Approver knows what they're approving (full content + context).
- [ ] Approver knows who will see the result and when.
- [ ] Reverse path exists or its absence is named.
- [ ] Result is logged in the activity feed.

# QUAY-Specific Questions

- The **internal dashboard**: if a staff member opens it for the first time on a Monday morning, what are the three actions they should take? Are those actions surfaced, or are they buried?
- The **client portal**: when a founder logs in at week 4 of their cohort, what do they see *first*? Is it celebrating their progress, listing their open tasks, surfacing a stuck proposal? What's the editorial point of view?
- The **proposal flow** in Slack: when a founder submits, do they get an acknowledgment with a timeline ("staff usually responds within 48 hours")? When a decision is made, do they get a Slack DM or just a portal change?
- The **weekly sentiment survey**: how is it framed? "How are you feeling?" feels casual; staff may use the data clinically. Is the framing aligned with use?
- **AI-generated proposals**: when staff reviews an AI-drafted proposal before sending, is it visually clear which parts came from AI vs which came from the founder's input?
- **Mentor intro flow**: when a mentor receives an intro request, is there enough founder context for them to decide, without overwhelming them?
- **Founder-as-staff confusion**: a staff member sometimes IS the founder of a partner company (the accelerator's portfolio model). Is the UI clear about which mode they're in? Or do they see both views overlapping?
- **Read.ai transcript summaries**: where are they shown? In a tab the founder visits? As a Slack message? As an email? Different surfaces imply different trust expectations.

# Common Failure Modes

- **The "no data" emptiness.** Empty states say "no activity yet" — fine. But a founder in week 4 with no activity has a problem; the empty state should reflect that, not normalize it.
- **The "you're doing great!" lie.** Sentiment summaries say positive things based on stale data. Founder trust collapses on the first time they catch it lying.
- **The polished demo trap.** Dashboard pixel-perfect; data behind it is a placeholder string. Stakeholders are reassured; operators learn nothing.
- **The "AI says..." problem.** AI output framed as if a human said it. When wrong, the AI's error becomes the platform's error in user perception.
- **The two-purpose dashboard.** Same page for staff overview and founder view. Staff get a feed too dense to read; founders get an interface too professional to feel personal.
- **The approval-without-context.** Staff sees "approve" button with no full proposal content; they approve by habit.
- **The unrecoverable destructive action.** "Are you sure?" "Yes." Now the entry is gone forever. (Soft-delete with undo is almost always better.)

# Anti-Patterns

- Designing for the happy path. The happy path doesn't need design; the sad paths do.
- Using "status" as a single string that conflates several meanings ("active" = "currently in cohort" AND "responding to surveys" AND "has uncompleted tasks").
- Empty states that hide rather than reveal — "no data to show" instead of "you haven't added anyone yet; here's how."
- Modal pop-ups for everything, training users to dismiss without reading.
- Two roles sharing a screen because "they need similar info" — they almost never need it the same way.

# Output Format

1. **Executive summary** — one paragraph: does QUAY's UI help users make decisions under stress, or just present information?
2. **Findings table** — surface, screen, audit element (primary action / empty / error / AI / approval / role-fit), severity, fix.
3. **Severity** per rubric.
4. **Evidence** — page path or Slack template name, screenshot description, the specific copy that fails.
5. **Recommended fix** — usually small: copy change, state design, label, confirmation step, role-split.
6. **Implementation complexity** — `trivial` to `small` for most UX fixes; `medium` if a surface needs to be split (one screen → two role-specific screens).
7. **Owner/surface affected** — `portal-internal`, `portal-client`, `slack-bot`.
8. **Follow-up questions** — product intent: should this surface be staff-only, what's the editorial tone for founders, etc.

# Example Prompt

> Audit QUAY's UX for trust and decision support per `skills/quay/genius-team/enterprise-ux-psychologist/SKILL.md`. Walk every user-facing screen and Slack message. For each, identify the primary user, primary action, and the four worst-moment states (loading, empty, partial, error). Audit every AI artifact for labeling and editability. Audit every approval/destructive flow. Emit findings per `FINDINGS_SCHEMA.md`. Do not change any UI. Append to current audit board.

# Related Skills

- [institutional-pm-reviewer](../institutional-pm-reviewer/SKILL.md) — defines whether the feature should exist; this skill assumes yes and asks if the UI works.
- [ai-governance-cost-optimizer](../ai-governance-cost-optimizer/SKILL.md) — AI labeling and human-gate rules.
- [institutional-qa-scenario-simulator](../institutional-qa-scenario-simulator/SKILL.md) — sad-path scenarios that exercise the UI under stress.
- [adversarial-operations-reviewer](../adversarial-operations-reviewer/SKILL.md) — user behavior that abuses the UI.
