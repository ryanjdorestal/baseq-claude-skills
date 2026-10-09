---
name: quay-platform-economics-analyst
description: Models QUAY's operating cost — per cohort, per founder, per AI artifact, per workflow run. Identifies scaling traps, free-tier ceilings, and the breakeven point where "automate it" is and isn't worth the spend.
---

# Purpose

QUAY's stack is a constellation of SaaS tools (Vercel, Supabase, n8n Cloud, Anthropic/OpenAI, Slack, Google Workspace, Read.ai). Each is cheap or free at today's scale. Combined and scaled to multiple clients, costs compound non-linearly. Worse, free-tier limits create silent failures: n8n Cloud execution caps, Supabase row/storage caps, Anthropic context-window caps.

This skill produces a **cost model** for QUAY today and at projected scale, identifies where money goes, names hidden ceilings, and gives ROI reasoning for every automation: "this is worth automating," "this saves no time and adds cost — don't automate yet," "this would be cheaper if you used a different tool."

# When to Use

- Every full audit, every `ai-cost` audit.
- When taking on a new client institution (multiply cohorts by clients).
- Before proposing a new automation — does the math work?
- When a SaaS bill triples and no one knows why.
- Quarterly, as a finance/runway hygiene step.

# Expected Inputs

1. Current SaaS bills (Vercel, Supabase, n8n Cloud, Anthropic, OpenAI, Slack, Google Workspace, Read.ai, any others).
2. Current usage levels: cohorts, founders, mentors, meetings/week, transcripts/week, AI calls/week, n8n executions/week.
3. Projected growth: cohorts in 3/6/12 months; founders per cohort; clients (institutions).
4. The AI policy table from `ai-governance-cost-optimizer`.

# Required Context to Inspect

- `package.json`, infra configs — what services are integrated.
- Pricing pages of all SaaS dependencies (recall — not necessarily live web fetch).
- The current activity feed volume (a proxy for total event throughput).

# Review Methodology

Build the cost model in three layers.

## Layer 1: Fixed monthly cost

Subscription floors that exist regardless of usage:
- Vercel team plan
- Supabase Pro (likely needed; free tier doesn't have backups/PITR)
- n8n Cloud tier
- Google Workspace seats (for staff)
- Slack workspace tier
- Read.ai plan
- Anthropic / OpenAI minimums (usually $0 minimums, but a few orgs require committed spend)

Total fixed/month: $X.

## Layer 2: Variable cost

Per-unit costs that scale with usage:
- AI tokens per type of artifact × volume.
- n8n Cloud executions over the included quota.
- Supabase database egress, storage, rows beyond the tier.
- Vercel function invocations, bandwidth.
- Slack messages (if applicable — usually generous).
- Drive / Workspace storage.

Build a per-unit-of-output cost:
- **Cost per cohort**: setup + ongoing per-cohort variable cost × cohort length.
- **Cost per founder**: variable cost attributable to one founder.
- **Cost per meeting transcript**: ingest + AI summary.
- **Cost per AI artifact** (proposal draft, intelligence note, intro suggestion).
- **Cost per workflow run**.

## Layer 3: Scaling

Project the cost model at:
- Today (1 cohort, N founders, current operations).
- 3 months out (assume +1 cohort).
- 6 months out (assume +2 cohorts, possibly +1 client).
- 12 months out (assume +1 client, +3-4 cohorts total).

Where does the curve become uncomfortable? At which scale does each SaaS tier need to be upgraded? Which one will surprise you first (free-tier silent cap)?

## Hidden ceilings to catalog

- **n8n Cloud execution count** — Cloud plans have monthly execution caps. Going over: either upgrades or stops running.
- **Supabase row/storage limits** — Free is 500MB; Pro is 8GB. Activity events compound; calculate the months-to-cap.
- **Vercel function execution time** — 60s per request on hobby/pro; AI calls that exceed this need to move out.
- **Anthropic / OpenAI rate limits** — workspace-level RPM/TPM. Spikes can cause failures and retry storms (handoff to `n8n-workflow-reliability-engineer`).
- **Slack rate limits** — sending too many DMs in too short a time.
- **Drive API quotas** — per-user and per-project query caps.

For each ceiling: current usage / ceiling = % consumed, and a projected month of breach.

## Automate-or-not reasoning

For each candidate automation, produce ROI math:
- Time saved per occurrence × occurrences per month = hours saved.
- Hours saved × hourly value of operator = $ value/month.
- Build cost (engineering time + AI cost + maintenance) = $.
- Breakeven month.

If breakeven > 12 months and the use case isn't strategic, **don't automate yet**. Add to the explicit "do-not-automate-yet" list with rationale.

# Severity System

- **P0** — Hidden ceiling that will be breached in the next 60 days with current trajectory; no plan in place. Or: an unbounded cost driver (e.g., AI fanout) with no cap.
- **P1** — Cost per cohort exceeds a defined budget. Free-tier ceiling within 6 months. Automation cost exceeds value but is being pursued.
- **P2** — Cost not attributable per cohort/per founder (you don't know unit economics). Hidden SaaS tier upgrade likely in 12 months.
- **P3** — Cost optimization opportunities that are nice-to-have (smaller model, cache hits, batch processing).

# Checklist

- [ ] Every SaaS dependency listed with current tier and monthly cost.
- [ ] Variable cost per unit (cohort, founder, transcript, AI artifact, workflow run) computed.
- [ ] Hidden ceilings catalogued with current % consumed and breach projection.
- [ ] Per-cohort cost model exists.
- [ ] Per-founder cost model exists.
- [ ] AI spend by feature (from `ai-governance-cost-optimizer`) integrated.
- [ ] 12-month cost projection at expected growth.
- [ ] Automate-vs-don't-yet list with ROI for each candidate.
- [ ] Cost alerts configured (handoff to `observability-telemetry-architect`).
- [ ] One operator owns watching costs monthly.

# QUAY-Specific Questions

- What's the cost of running ONE cohort end-to-end today (12 weeks, 15 founders, weekly check-ins, transcript ingestion, weekly surveys)?
- If a paying client wants 3 cohorts of 20 founders next year, what does that cost in stack expenses?
- Read.ai costs per meeting: is that paid by QUAY, the founder, or shared?
- Is Google Workspace billed per staff seat, founder seat, both, or neither (founders use their own Google)?
- Are AI artifacts being regenerated unnecessarily (e.g., the same transcript summarized weekly)? Each is a cost line.
- Is the activity feed write rate growing faster than expected? Storage compounds.
- Is n8n Cloud or self-hosted? Cloud has execution-count caps; self-hosted has DevOps cost.
- Is there a Vercel team plan today? Edge function invocations are cheap but not free.
- Is the Supabase project on Pro tier? Free tier auto-pauses inactive projects — that would be a P0 production risk.

# Common Failure Modes

- **The free-tier surprise.** Supabase free-tier project pauses; production becomes unreachable. Or n8n free tier executions cap mid-month; workflows just stop.
- **The AI fanout.** Daily cron generating per-founder summaries seems cheap at 1 cohort, then there are 3 cohorts, then it's 50× the cost overnight.
- **The unbounded retry.** A failing workflow retries forever. Cost accrues per attempt.
- **The "cache miss every time" pattern.** Cache configured for 60 seconds, requests at 70-second intervals — cache never hits, cost never drops.
- **The "tooling for tooling's sake" cost.** Three observability tools at $X/mo each, two used, one forgotten. Sum is non-trivial.
- **The migration that wasn't.** Project is on a free trial of a SaaS; trial ends; auto-upgraded to the most expensive tier silently.

# Anti-Patterns

- "We'll figure out costs when we're bigger." Costs that scale non-linearly punish this.
- "It's a one-time thing." Most one-time things become every-week things.
- "AI is cheap." Per call, yes. Per month at scale, no.
- "We can always switch." Switching costs (migrations, integrations, retraining team) compound.
- Comparing only sticker price between tools while ignoring time-to-implement and ongoing maintenance.

# Output Format

1. **Executive summary** — one paragraph: what does QUAY cost today, what does it cost at 3× scale, what's the next ceiling.
2. **Cost model table** — fixed/variable/per-unit. The headline artifact.
3. **Hidden ceilings table** — ceiling, current consumption, projected breach month.
4. **12-month projection** — costs at each milestone.
5. **Automate-or-not list** — per candidate, with ROI reasoning.
6. **Findings table** — concern, severity, fix.
7. **Severity** per rubric.
8. **Evidence** — bill screenshots (described), usage data, pricing references.
9. **Recommended fix** — set up cost alerts; switch to cheaper model where appropriate; defer Y automation; consolidate Z tools.
10. **Implementation complexity** — usually `small` for switching/configuration; `medium` for moving off a SaaS.
11. **Owner/surface affected** — `economics`, `ai`, `n8n`, `observability`.
12. **Follow-up questions** — about per-client pricing model (if applicable) and acceptable per-cohort cost.

# Example Prompt

> Build the QUAY cost model per `skills/quay/genius-team/platform-economics-analyst/SKILL.md`. List every SaaS dependency, compute variable cost per cohort and per founder, project costs at 3/6/12 months. Identify hidden ceilings and the order in which they'll be hit. Produce the automate-or-not list with ROI for current and proposed automations. Emit findings per `FINDINGS_SCHEMA.md`. Do not change any config or billing. Append to current audit board.

# Related Skills

- [ai-governance-cost-optimizer](../ai-governance-cost-optimizer/SKILL.md) — AI cost is the most volatile line item.
- [n8n-workflow-reliability-engineer](../n8n-workflow-reliability-engineer/SKILL.md) — workflow execution counts and retry storms.
- [observability-telemetry-architect](../observability-telemetry-architect/SKILL.md) — cost alerts as a signal.
- [product-scope-ruthless-prioritizer](../product-scope-ruthless-prioritizer/SKILL.md) — automate-or-not list informs scope.
- [handoff-maintainability-engineer](../handoff-maintainability-engineer/SKILL.md) — fewer tools, fewer bills, easier handoff.
