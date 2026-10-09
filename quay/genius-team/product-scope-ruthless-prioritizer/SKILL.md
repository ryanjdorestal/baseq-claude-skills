---
name: quay-product-scope-ruthless-prioritizer
description: Sorts the audit's findings into a sprint plan — what must ship before handoff, what to scaffold, what to cut, what to document instead of build. Forces P0/P1/P2/P3 decisions and produces the kill list.
---

# Purpose

Every audit produces more findings than the team can fix. Without prioritization, three things go wrong: real P0s get diluted by P3s; the team chases shiny features instead of fundamentals; tech debt gets written into the foundation by attempts to ship everything at once. This skill is the final reviewer in an audit. It looks at all findings produced by all other skills and converts them into one actionable plan: P0/P1/P2/P3 priorities, kill list, defer list, and "document instead of build" list.

# When to Use

- The last skill to run in every full and handoff audit.
- Standalone in `quick` audit when the goal is just "what should we do next."
- Before any sprint planning.
- When the team feels overwhelmed by feature requests / audit findings.

# Expected Inputs

1. **All findings from the current audit board.**
2. The intended QUAY trajectory — handoff date, planned client onboardings, sprint cadence.
3. Team capacity — how many engineer-hours per week are realistically available.
4. Any externally-committed dates (a client demo, a stakeholder review).

# Required Context to Inspect

- The current audit board.
- Existing backlog (Linear / Notion / Sheets — wherever the team tracks work).
- The platform's current state of operability (is the platform shipping value today, or just promising it).

# Review Methodology

Apply five filters, in order. Findings move through the filters until they land in a bucket.

## Filter 1: Is it a real P0?

Re-validate P0 severity using the `FINDINGS_SCHEMA.md` rubric. If the finding doesn't meet the rubric, downgrade. Inflate kills the system.

After this filter: at most 5 P0s.

## Filter 2: Does the fix produce leverage?

For each P0 and P1: does fixing it unlock further work, prevent future incidents, or remove ongoing operational drag? Leverage > local optimization.

Example: "Add RLS to tasks table" has high leverage — it unblocks opening the founder portal externally. "Rename a column" has low leverage.

## Filter 3: Is the cost worth it now?

For each remaining finding: cost-to-fix (per task estimate) vs benefit (severity + leverage). Defer where benefit < cost in this sprint horizon.

## Filter 4: Can it be cut instead of fixed?

For each finding: is the underlying feature worth keeping? If a feature only exists because it was demo polish or speculative scope, **cutting** it removes the finding entirely. This is the kill list — and it's usually the highest-leverage action available.

## Filter 5: Should it be documented instead of built?

For each finding that recommends new tooling/automation/feature: is the manual process actually fine? Document the manual process; defer the automation. Many findings dissolve when the team accepts "this is fine to do by hand for now, just write down how."

## Bucket assignment

After the filters, every finding lands in one bucket:

- **P0 (now)** — must ship in this sprint. Hard cap of 5.
- **P1 (this sprint)** — should ship in this sprint.
- **P2 (next sprint)** — queued for the next sprint with target date.
- **P3 (backlog)** — recorded, not promised.
- **Kill list** — the underlying feature/code should be removed; the finding evaporates.
- **Defer list** — explicitly not doing it this audit cycle; has a `defer_until` date.
- **Document instead of build** — the manual process is written down; no automation is built.
- **Waived** — accepted as risk with `waived_until` expiration.

# Severity System

This skill **doesn't emit new findings with severities**. It re-validates and reassigns severities to other skills' findings. Its own outputs are the buckets above.

Meta-finding categories (emitted as findings against the audit itself):

- **Inflation finding** — when other skills proposed more than 5 P0s, this skill flags it and proposes a downgrade rationale.
- **Leverage gap** — a finding marked low severity but with high leverage; this skill upgrades.
- **Documentation-instead-of-build candidate** — flagged when a finding recommends automation and the manual process is fine.

# Checklist

- [ ] Every finding from the audit has a bucket.
- [ ] P0 count ≤ 5.
- [ ] Kill list named with at least one item if the audit ran across the whole platform.
- [ ] Defer list items all have `defer_until` dates.
- [ ] Waivers all have `waived_until` dates and approvers.
- [ ] "Document instead of build" items have a target doc location.
- [ ] Total estimated sprint effort fits in the team's actual capacity (with buffer for unknowns ≥ 20%).
- [ ] Handoff-critical items (from `handoff-maintainability-engineer`) are P0 or P1 if handoff is within 60 days.
- [ ] No P3 is sneaking into the sprint plan.

# QUAY-Specific Questions

- Is Ryan's involvement still expected to be full-time, part-time, or ending in N weeks?
- Is a paying client expected before September? If so, the multi-tenant boundary findings are P0 regardless of intrinsic severity.
- Are there features that exist solely because Ryan built them in a flow state and they were never asked for? Strong candidates for kill list.
- Are there workflows that staff has already stopped using? Kill them rather than fix them.
- For each AI feature: is it worth its monthly cost given current usage? If not, defer or kill.
- Of all the Genius-Team skills' findings, which ones would *not* matter if Ryan stayed full-time for 12 more months? Those are deprioritized vs the handoff-critical set.
- What's the dumbest, smallest thing that would meaningfully improve operations this week? That's a P0/P1 candidate regardless of severity.

# Common Failure Modes

- **The "everything is P1" trap.** When P1 has 25 items, none of them are P1 — the bucket lost meaning.
- **The "we'll get to it" defer.** Defer with no date is a quiet kill but without honesty. Date it or kill it.
- **The "we'll automate it" reflex.** Automation reduces ongoing cost but costs upfront. If the volume is low, don't automate; document the manual process.
- **Sprint plans that don't survive contact with reality.** Always under-commit; aim for 70% of capacity, not 100%.
- **The "feature creep through the audit" pattern.** Reviewers slip in unrelated improvements as P3 findings. This skill should reject those.

# Anti-Patterns

- Treating audit output as inviolable. Audits propose; the team disposes. Override severities with rationale when warranted.
- Refusing to kill features because "someone might want it later." If no one is asking, kill it and document the gap so it can be rebuilt if needed.
- Sprint plans that include items with `do-not-fix-yet` flags. Those flags exist for a reason; respect them.
- Building automation before the manual process has been done enough to understand the variation.
- Counting "write a doc" as the entire fix when the underlying problem is technical.

# Output Format

This skill produces the **prioritization section of the audit board** (per `AUDIT_OUTPUT_TEMPLATE.md` sections 5–12).

Specifically:
1. **Executive prioritization summary** — one paragraph: what this sprint accomplishes, what it explicitly doesn't, what gets killed.
2. **P0 list** — re-validated, ≤ 5 items.
3. **P1 list** — sprint commitment.
4. **P2 list** — next-sprint queue, with target dates.
5. **P3 list** — backlog only.
6. **Kill list** — features/code to delete with rationale.
7. **Defer list** — items with explicit `defer_until` dates.
8. **Document-instead-of-build list** — manual-process docs to write, with target locations.
9. **Waiver list** — items accepted as risk with `waived_until`.
10. **Capacity reconciliation** — sum of estimates vs team capacity. If over, explicitly cut.
11. **Risk register** — risks the prioritization itself creates (e.g., "by deferring observability, we accept that some failures will be invisible for one more sprint").
12. **Recommended next sprint** — one paragraph (per `AUDIT_OUTPUT_TEMPLATE.md` §16).

This skill does **not** emit new findings with evidence/files — it operates on the findings other skills produced. Any meta-finding it emits (severity inflation, leverage gap) is a `category: skill-gap` or `category: product-scope` finding.

# Example Prompt

> Run the QUAY scope prioritization per `skills/quay/genius-team/product-scope-ruthless-prioritizer/SKILL.md`. Take all findings from the current audit board. Re-validate severities. Apply the five filters. Assign every finding to a bucket: P0 / P1 / P2 / P3 / Kill / Defer / Document-instead / Waive. Produce the prioritization sections (5–12 plus §16) of the audit board. Ensure P0 count ≤ 5. Reconcile total estimate against team capacity. Append to current audit board as the final step.

# Related Skills

- [institutional-pm-reviewer](../institutional-pm-reviewer/SKILL.md) — provides the "is this feature worth defending" reasoning that feeds the kill list.
- [handoff-maintainability-engineer](../handoff-maintainability-engineer/SKILL.md) — handoff-critical items upgrade severity here.
- [platform-economics-analyst](../platform-economics-analyst/SKILL.md) — automate-vs-don't-yet recommendations feed this skill.
- All other skills — their findings are this skill's input.
