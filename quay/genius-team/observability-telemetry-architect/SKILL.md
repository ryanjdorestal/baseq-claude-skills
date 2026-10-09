---
name: quay-observability-telemetry-architect
description: Defines what QUAY operators need to see to know the platform is healthy, what alerts when, and what dashboards prove operational. Converts vibes ("things feel slow") into measurable signals tied to user impact.
---

# Purpose

QUAY today is observable mostly by Ryan opening tabs and checking n8n executions, Supabase logs, and Slack. That doesn't scale beyond one operator. The platform needs **operator-facing dashboards** for staff (event counts, workflow latency, failure rates, AI spend, survey completion) and a **paging/alerting layer** for incidents (workflow stalled, ingestion blocked, AI budget breached).

This skill specifies what to measure, where it surfaces, what thresholds page, and what stays as a quiet background signal. It also identifies what's NOT measured today (the dark surfaces).

# When to Use

- Every full audit; every `handoff` audit (handoff is impossible without observable operations).
- When a new feature ships — what should the operator see about it.
- When an incident occurred — what would have surfaced it sooner.
- When an alert is too noisy or too quiet.
- When onboarding a new operator/staff member.

# Expected Inputs

1. Existing dashboards or status pages (likely few or none).
2. The list of n8n workflows and their execution histories.
3. Supabase log access patterns.
4. AI provider usage logs.
5. Slack channels used for ops chatter.

# Required Context to Inspect

- Internal portal pages (`portal-internal`) — is there an "operations" or "health" page already?
- `skills/quay/internal-dashboard/SKILL.md` — what the dashboard claims to show.
- n8n execution log retention settings.
- Supabase observability config.
- Anything labeled "monitoring," "metrics," "health" in the repo.

# Review Methodology

For each operational concern, produce an **observability entry**:

```
concern: <e.g., "Read.ai transcript ingestion is processing>
metric: <count / rate / latency / cost — concrete unit>
collection_point: <where the data comes from — Supabase query, n8n log, AI provider API>
refresh_cadence: <real-time, 5min, hourly, daily>
surface: <portal-internal page, Slack alert channel, email digest>
threshold_warn: <value triggering a soft warning>
threshold_page: <value triggering a paging alert>
owner_when_pages: <role or person>
runbook: <link to the playbook for handling this alert>
```

Anything without surface, threshold, owner, or runbook is a finding.

## The four golden signals (adapted from SRE)

For each user-impacting surface, define:

1. **Traffic** — how many events are flowing? (Slack messages handled, transcripts ingested, founders active this week.)
2. **Errors** — what's failing? (n8n DLQ depth, 5xx rate, AI call failures.)
3. **Latency** — how long? (Transcript ingestion p50/p95, Slack response time, AI summary turnaround.)
4. **Saturation** — what's getting full? (Token budget vs spend, queue depth, Drive storage, Supabase row counts trending wrong.)

## What staff vs founders see

- **Staff** see ops signals — DLQ depth, AI spend, ingestion latency, error rates.
- **Founders** see **product** signals — their own activity, their own cohort's events. They do NOT see ops metrics.
- **Mentors** see assigned-founder activity, nothing else.
- The dashboard for staff is the operator surface; client/founder portals are not status pages.

## Alert quality

- A page that fires when nothing is broken is worse than no page (alarm fatigue).
- An alert with no runbook is a notification, not an alert.
- An alert with no owner is no one's job.
- An alert that fires more than once a day for the same cause needs aggregation or auto-resolution, not louder noise.

# Severity System

- **P0** — Any of:
  - A user-impacting failure mode has **no detection** — staff find out via founder complaint.
  - The platform has no health dashboard at all, and operators must guess.
  - AI spend has no measurement; budget breach would only surface on the provider bill.
  - n8n DLQ (or its equivalent) has no surface — failed events are silently lost from operator view.
- **P1** — Detection exists but is buried (need to SQL-query Supabase to know about a failure). No paging — everything is "check if you remember to look." Alerts exist but have no runbook.
- **P2** — Dashboards exist but show metrics that don't tie to user impact (vanity metrics). Some alerts but noisy. Refresh cadence too slow for the concern.
- **P3** — Dashboard panels uninformative names. Alert messages lack context. Runbooks exist but are stale.

# Checklist

- [ ] Staff have a single "operations" page (in the internal portal or external dashboard tool) showing health at a glance.
- [ ] Four golden signals named for each user-impacting surface.
- [ ] Per concern: metric, collection point, refresh cadence, surface, thresholds, owner, runbook.
- [ ] n8n DLQ depth (or `workflow_dead_letters` row count by status) visible.
- [ ] AI spend dashboard: today's spend, MTD spend, projected month, % of budget.
- [ ] Transcript ingestion: count today, failed count today, oldest pending.
- [ ] Proposal flow: drafts today, submitted today, decisions overdue (older than X).
- [ ] Slack survey: sent today, completed today, response rate this week, "red" responses needing follow-up.
- [ ] Auth: login attempts, login failures, role changes (audit log query) accessible.
- [ ] Founder activity per cohort: active vs lapsed.
- [ ] Alerts route to a defined channel (`#ops-alerts`) and have an on-call owner today (even if it's just Ryan, name them).
- [ ] No alert lacks a runbook link.

# QUAY-Specific Questions

- Today, when an n8n workflow fails three times and dead-letters an event, **how does Ryan find out?** If the answer is "checks n8n manually," that's P0.
- Today, when AI spend doubles week-over-week, **how does Ryan find out?** If the answer is "checks the Anthropic dashboard occasionally," that's P0.
- Today, when a founder fails to receive their weekly survey, **how does staff find out?** Same question pattern.
- Is there a "first 5 minutes of the morning" dashboard a staff member checks before standup? If not, what would it show?
- The activity feed: is it a feed (people read it) or a database (people query it)? If a feed, what's the engagement model — does staff actually look at it?
- The Base44 dashboards: are they functional, or visual placeholders? If placeholders, that's worth a finding.

# Common Failure Modes

- **The dashboard nobody opens.** Pretty page, no one consults it before decisions. Effective monitoring zero, but it gives false confidence.
- **The vanity dashboard.** Total events, total users, total AI calls. Big numbers, no operational signal — none of them tell you whether anything is wrong.
- **The siloed log.** Logs are in Supabase, AI logs in Anthropic, workflow logs in n8n, Slack messages in Slack. Incident: "transcript missing for cohort 3 Monday meeting." Diagnosis requires cross-correlating four tools.
- **The "we'll check it" alert.** An alert exists; it fires into an unmonitored email. No one's reading.
- **The threshold-by-vibe.** Alert fires at "high" spend with no number. Either too noisy or too quiet, never right.
- **The page without a runbook.** "Workflow X failed" — okay, what do I do? If the page doesn't link to a doc, the page is a panic generator.

# Anti-Patterns

- "We'll add observability after we ship." Production without observability is hope-driven.
- Building a dashboard with 40 panels because more is better. 5 panels, each one operationally meaningful, is better.
- Alert escalation paths that go to one person 24/7 with no rotation.
- Storing dashboards in Notion as screenshots that drift from reality.
- Conflating product analytics (how many founders submitted proposals) with operational telemetry (how many proposal-submit workflows failed).

# Output Format

1. **Executive summary** — one paragraph: does staff have the means to know the platform is healthy without asking Ryan? Specific dark surfaces named.
2. **Observability entries table** — one row per concern with the fields above.
3. **The four golden signals matrix** — for each user-impacting surface, traffic / errors / latency / saturation, with current vs target measurement state.
4. **Findings table** — concern, gap, severity, fix.
5. **Severity** per rubric.
6. **Evidence** — current dashboard URLs (or absence), example incident that was missed for hours/days.
7. **Recommended fix** — specifically: build this panel in the internal portal at this path, write a Supabase query that returns this, configure n8n's error-workflow to post to `#ops-alerts`.
8. **Implementation complexity** — `small` for a query + panel; `medium` for full dashboard pages; `large` for adopting an external tool (Grafana, etc.).
9. **Owner/surface affected** — `observability`, `portal-internal`, `n8n`, `docs` (runbooks).

# Example Prompt

> Audit QUAY's observability per `skills/quay/genius-team/observability-telemetry-architect/SKILL.md`. List every operational concern that needs a signal. For each, declare metric / source / surface / thresholds / owner / runbook — and flag the missing pieces. Build the four-golden-signals matrix per surface. Emit findings for dark surfaces (no detection at all). Do not change any code. Append to current audit board.

# Related Skills

- [n8n-workflow-reliability-engineer](../n8n-workflow-reliability-engineer/SKILL.md) — workflow failure signals.
- [ai-governance-cost-optimizer](../ai-governance-cost-optimizer/SKILL.md) — AI spend signals.
- [handoff-maintainability-engineer](../handoff-maintainability-engineer/SKILL.md) — runbooks live where this skill points.
- [adversarial-operations-reviewer](../adversarial-operations-reviewer/SKILL.md) — abuse signals (rapid-fire submissions, anomalous logins).
- [enterprise-ux-psychologist](../enterprise-ux-psychologist/SKILL.md) — what staff dashboards must NOT look like to founders.
