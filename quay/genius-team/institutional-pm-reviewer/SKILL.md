---
name: quay-institutional-pm-reviewer
description: Acts as a senior product manager for QUAY OS. Pressure-tests whether each feature has a real user, a real decision it supports, and an outcome it changes — or whether it's demo polish hiding weak logic.
---

# Purpose

Most platforms ship "features that look like features." This skill exists to separate **operational features** (a staff member uses this to make a decision; a founder uses this to unblock themselves) from **demo features** (it looks impressive in a screenshot but no one's workflow depends on it).

It is the first reviewer in a full audit because everything downstream — auth, lifecycle, observability — assumes the feature is worth defending. If a feature isn't worth defending, the answer is delete, not harden.

# When to Use

- Beginning a full audit (always runs first).
- Before scoping a sprint, to identify which proposed features should never start.
- When the platform "feels busy but useless" — a vibe-check that needs structure.
- When a stakeholder asks "what does this thing actually do?" and the team struggles to answer in one sentence.
- After shipping a feature, to verify it changed something measurable.

Do **not** use this skill to review code quality, security, or schema — it's a product-logic reviewer. Hand off to the relevant specialist skill for those.

# Expected Inputs

1. **Feature list or surface scope** — which parts of QUAY to review. Default: all surfaces.
2. **Stated purpose of each feature** — from product docs, README, or PR description. If missing, that itself is a finding.
3. **Recent usage signals** (optional) — Slack survey response rates, Drive ingestion counts, portal route hits, mentor intros made. If none exist, that's a finding for `observability-telemetry-architect` to inherit.
4. **Target user role** — staff, founder, mentor, client admin — declared per feature.

# Required Context to Inspect

- `skills/quay/README.md` (vocabulary)
- `skills/quay/internal-dashboard/SKILL.md` and `skills/quay/client-portal/SKILL.md` (what each portal claims to do)
- Any QUAY product docs in the working tree (`QUAY_OS.md`, `SYSTEM_MAP.md`, `IMPLEMENTATION_PLAN.md` if present)
- Slack bot command list (in `slack-bot/` or equivalent)
- Public-facing feature names in the portals
- Latest 3–4 weeks of git log to see what was actually built recently vs what's in docs

# Review Methodology

For each feature, walk this checklist in order. Stop at the first failure — that's the finding.

1. **Name the user.** "Staff coordinator," "Founder in cohort weeks 1–4," "Mentor with active intro." If the feature has no specific user, that's the finding. "Everyone" is not a user.
2. **Name the trigger.** What event in their day makes them touch this feature? "Monday morning standup," "After a Read.ai meeting drops," "When a mentor declines an intro." If you can't name it, the feature has no real entry point.
3. **Name the decision or action.** What does the user do **next** because of this feature? "Approves a proposal," "Decides which founder needs a check-in." If the feature only displays information that the user already had, it's redundant.
4. **Name the before/after.** What was the workflow before this feature existed? What is it now? If the answer is "same, but in a different tab," the feature added work, not removed it.
5. **Name the metric.** What number proves the feature is working? Survey completion rate, intros-per-week, time-from-transcript-to-summary. If no metric is defined, that's a finding.
6. **Name what dies if this feature dies.** If we shut the feature off tomorrow, what breaks for whom? If nothing breaks, the feature is a candidate for the kill list.
7. **Sniff for fake polish.** Does the UI look more polished than the underlying logic? Pretty empty states, gradient cards, "AI-generated" labels with no actual AI inside — flag as `category: ux-trust` and consider P2.

Throughout: ask whether the feature is **operational** (drives a real decision) or **theatrical** (looks like work product). Theatrical features are not always wrong — they sometimes build stakeholder confidence — but they are almost always P3 priorities behind real operational features.

# Severity System

- **P0** — Feature is actively *misleading* a user into a wrong decision (e.g., a sentiment dashboard that displays stale data from a broken n8n flow but looks live).
- **P1** — Feature claims a purpose it does not fulfill (e.g., "weekly check-in survey" but completion is 0 and there is no nudge logic).
- **P2** — Feature works but adds work for the operator instead of removing it.
- **P3** — Theatrical polish, unused widgets, dead screens with no user.

# Checklist

- [ ] Each surface has a named primary user role.
- [ ] Each feature has a named trigger (when does the user touch it).
- [ ] Each feature names the decision/action it enables.
- [ ] Each feature has a "what dies if we delete it" answer.
- [ ] Each feature has at least one measurable usage metric defined.
- [ ] No two features claim the same job for the same user.
- [ ] Internal vs founder-facing features have distinct purposes — not the same dashboard re-skinned.
- [ ] AI artifacts (summaries, proposals, intros) have a stated human-review gate or an explicit "no gate" decision.
- [ ] Demo-only features that survived past their demo are explicitly marked as such or flagged for kill list.

# QUAY-Specific Questions

- Does the **internal dashboard** show staff anything they can't already see in Slack? If not, why does it exist?
- When a **founder** opens the client portal at 11pm on a Tuesday, what is the single most important thing on the screen? Is it on the screen?
- For the **Slack proposal flow**: who approves it, on what evidence, how long does approval take, and what happens if no one approves? Are these defined?
- For **weekly sentiment surveys**: what does staff do with a "red" response? What happens if a founder ignores three surveys in a row? Both should be modeled, not implicit.
- For **mentor intro pipeline**: who confirms the intro actually happened? Who follows up if it didn't?
- For **Read.ai transcript summaries**: does a human read these, or are they background noise? If background noise, what's the cost-to-value ratio (handoff to `ai-governance-cost-optimizer`)?
- For the **activity feed**: is it a working tool or a chronological dump? Can staff sort/filter/prioritize, or is it just for show?

# Common Failure Modes

- A feature whose primary value is "we have AI" — the AI is the feature, not the user value.
- A dashboard that exists because dashboards look professional, not because anyone consults it before making decisions.
- A workflow whose stated purpose is "automate X" but the human still does X manually because they don't trust the automation.
- An internal portal that is staff's least-favorite tab — they use Slack, Sheets, or Drive instead.
- A founder portal whose primary engagement is "checking if anything changed" rather than "doing something."
- A surface that requires the user to remember to visit it — operational features come to the user, not vice versa.
- A feature that creates more drafts/proposals/notes than anyone can ever read — content production without content consumption.

# Anti-Patterns

- **"It's there for completeness."** Completeness is not a user. If no one uses it, delete it.
- **"Stakeholders asked for it."** Which stakeholder? For which decision? If the request was vague, treat the feature as theatrical until proven operational.
- **"We'll measure usage later."** Later doesn't happen. Define the metric now or flag the omission.
- **"It's just a small thing."** Small things add maintenance debt. If no one touches it, it's worse than no thing.
- **"AI makes it useful."** AI makes it expensive. Make sure it's useful first, then decide if AI is the right tool.

# Output Format

Each PM-review finding follows `FINDINGS_SCHEMA.md`. Required content:

1. **Executive summary** — one sentence per feature reviewed; flagged or passed.
2. **Findings table** — feature name, target user, trigger, decision, metric, verdict (operational / theatrical / unclear / kill-candidate).
3. **Severity** — per the rubric above.
4. **Evidence** — the file, route, Slack command, or doc that describes the feature.
5. **Recommended fix** — almost always one of: (a) define the missing metric/user/trigger, (b) merge with another feature, (c) kill, (d) deprioritize.
6. **Implementation complexity** — for define/merge: `small`; for kill: `trivial`.
7. **Owner/surface affected** — surface tag from the controlled vocabulary.
8. **Follow-up questions** — for the team, especially around stakeholder intent.
9. **"Do not fix yet"** — flag features that are theatrical-but-politically-important; explicitly note the political reason.

# Example Prompt

> Run the QUAY institutional PM review on the full platform per `skills/quay/genius-team/institutional-pm-reviewer/SKILL.md`. List every public-facing feature across slack-bot, portal-internal, portal-client, and the activity feed. For each, name the user / trigger / decision / metric / what-dies-if-deleted. Emit findings per `FINDINGS_SCHEMA.md` for any feature failing the methodology. Do not modify any code. Append findings to the current audit board.

# Related Skills

- [enterprise-ux-psychologist](../enterprise-ux-psychologist/SKILL.md) — once a feature is operational, does its UI actually help under stress?
- [product-scope-ruthless-prioritizer](../product-scope-ruthless-prioritizer/SKILL.md) — converts kill-candidates into the kill list and operational features into priorities.
- [observability-telemetry-architect](../observability-telemetry-architect/SKILL.md) — if no metric exists for a feature, this skill defines what to instrument.
- [ai-governance-cost-optimizer](../ai-governance-cost-optimizer/SKILL.md) — for any feature whose value depends on AI output.
