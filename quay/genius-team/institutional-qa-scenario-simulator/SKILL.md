---
name: quay-institutional-qa-scenario-simulator
description: Produces realistic end-to-end scenarios — happy path, sad path, edge case, partial failure, race conditions — that pressure-test QUAY's surfaces. Each scenario has explicit expected behavior, failing conditions, and a manual vs automated test recommendation.
---

# Purpose

QUAY's "tests" today are mostly Ryan running through flows manually. That doesn't catch race conditions, partial failures, duplicate submissions, or weird-data-state edge cases that production will eventually hit. This skill produces a **scenario library**: structured tests that describe what to do, what should happen, and what counts as failure — automated where possible, manual where not.

# When to Use

- Every full audit; `pre-deploy` audit (regression scenarios for changed surfaces); `quick` audit.
- After a real incident — convert it into a scenario so it never recurs silently.
- Before opening any surface to external users.
- When adding any new cross-system flow.

# Expected Inputs

1. The surface or flow under test (Slack proposal submit, transcript ingest, founder magic-link login, etc.).
2. The state machines from `lifecycle-state-machine-auditor`.
3. The boundary matrix from `multi-tenant-boundary-architect`.
4. The known abuse cases from `adversarial-operations-reviewer`.

# Required Context to Inspect

- The code path under test.
- Sample real-world data shapes (so scenarios use realistic values, not placeholders).
- The current test suite if any.

# Review Methodology

For each flow, produce scenarios in the following five categories. Each scenario follows this shape:

```
id: S-001
title: <short imperative>
flow: <which user flow>
category: happy | sad | edge | partial | race
preconditions: <what state the system must be in>
actor: <which role + sometimes specific identity, e.g., "Founder in Cohort 3 week 4">
steps:
  1. ...
  2. ...
expected_outcome:
  - <observable behavior 1>
  - <observable behavior 2>
failing_conditions:
  - <if any of these is true, the scenario fails>
priority: P0 | P1 | P2 | P3
test_type: automated (suggested: unit / integration / e2e) | manual
automation_owner: <team or "after-MVP">
notes: <gotchas, data setup, environment>
```

## Category 1: Happy path

The intended flow with everything working. Cheap to test; should be automated.

Examples for QUAY:
- Staff approves a proposal in the internal portal; founder receives Slack notification; activity event recorded.
- Read.ai webhook fires; transcript ingested; AI summary generated; row created; Slack post made.
- Founder submits proposal via Slack; row created; staff sees in queue.

## Category 2: Sad path (user-driven)

The user does something allowed but undesired.

- Founder submits proposal then immediately withdraws it.
- Founder submits the same proposal twice (same content; UI didn't load fast enough).
- Staff approves then rejects within 1 minute.
- Mentor declines an intro request; founder requests a different mentor.
- Founder requests data deletion (today: no automation — make this a manual runbook scenario).

## Category 3: Edge case

Realistic-but-rare data or state combinations.

- A founder name with emoji and a curly apostrophe.
- A proposal description with 50,000 characters.
- A transcript meeting with 20 participants, half not in QUAY.
- A cohort with 1 founder; a cohort with 50.
- A mentor profile with no email.
- A timezone-edge meeting at 23:59 UTC on the last day of a cohort.
- A founder who completed Cohort 2, was archived, and is being re-added to Cohort 5.
- An n8n workflow execution that starts in week N and the workflow definition is edited mid-execution.

## Category 4: Partial failure

A step in a multi-step flow succeeds; the next fails.

- Proposal row written to Supabase; Slack post fails.
- Transcript ingested; AI summary fails; what's in the row?
- Mentor intro created in Supabase; calendar invite fails to send.
- Webhook from Read.ai received; n8n workflow times out at the AI step.
- Magic-link email sent; email delivery to founder's inbox bounced.
- AI provider returns 429; retry hits 429 again.

For each, ask: **does the system end in a consistent state, and does the operator know?**

## Category 5: Race condition

Two events arriving close in time produce a defect.

- Two webhooks for the same transcript arriving within milliseconds (Drive can do this).
- Staff approves a proposal at the same moment a founder withdraws it.
- Two Slack interactions on the same proposal modal from two staff members.
- A weekly survey scheduled-send fires at the same instant a founder is being offboarded.
- n8n executes the same workflow twice (manual re-run while a scheduled run is in flight).

# Severity System

(For the priority of the scenario itself.)

- **P0** — Scenario reproduces a known dangerous defect; or scenario tests a P0 abuse case from `adversarial-operations-reviewer`; or scenario tests an auth/boundary edge case where a failure means data leak. These must be automated.
- **P1** — Scenario tests a partial-failure path that today has no consistent-state guarantee. Automate where feasible; otherwise add a runbook entry.
- **P2** — Scenario tests an edge case that hasn't broken yet but could. Add to manual QA checklist or backlog automation.
- **P3** — Scenario is a polish-grade sanity check.

# Checklist

- [ ] For every user-facing flow, ≥ 1 happy-path scenario exists.
- [ ] For every flow, ≥ 1 sad-path scenario exists.
- [ ] For every flow with multiple side effects, ≥ 1 partial-failure scenario exists.
- [ ] For every flow with concurrent triggers, ≥ 1 race scenario exists.
- [ ] Every scenario has preconditions, steps, expected outcome, failing conditions, priority.
- [ ] Every P0 scenario has an automated test (or a written, dated commitment to add one).
- [ ] Every failure mode found in `lifecycle-state-machine-auditor` has a corresponding scenario.
- [ ] Every abuse case from `adversarial-operations-reviewer` has a scenario (testing the prevention).
- [ ] Scenarios use realistic data shapes (real-ish names, dates, lengths, emoji), not `foo/bar/baz`.

# QUAY-Specific Questions

- For the **proposal submit flow**: walk through founder writes draft, submits, edits while in review, withdraws, re-submits. Each step a scenario.
- For the **transcript ingest flow**: walk through Drive new file, Read.ai webhook duplicate, AI failure, Slack post failure. Each a scenario.
- For the **mentor intro flow**: walk through request, mentor declines, mentor accepts but no-show, mentor accepts and meets. Each a scenario.
- For the **founder onboarding**: walk through invite sent, invite link expired before click, link clicked twice, founder's email changes mid-cohort.
- For the **weekly survey**: walk through sent successfully, founder ignores, founder ignores three weeks in a row, founder responds "red", staff response loop.
- For **staff-as-founder view**: walk through staff toggles view, navigates founder pages, attempts a destructive action — what should happen.
- For the **activity feed**: walk through 1,000 events generated in a day — does the UI degrade? Does pagination work?

# Common Failure Modes

- Scenarios that test only the happy path. The happy path always works in dev.
- Scenarios with vague expected outcomes ("it should work").
- Scenarios that depend on running in a specific order; flaky and impossible to parallelize.
- Scenarios that are written once and not maintained — the code changes, the test still passes for the wrong reason.
- "Manual QA" being the entire test plan. Manual QA doesn't scale and doesn't catch regressions silently.

# Anti-Patterns

- Mocking the database in integration tests for paths whose correctness depends on RLS or constraints. Use a real (test) database.
- Asserting on exact log output. Logs change; the assertion is brittle.
- Using a single shared test user across all scenarios. Tests interact silently through that user.
- Tests that fail "sometimes" being marked flaky and disabled rather than diagnosed.

# Output Format

1. **Executive summary** — one paragraph: how many scenarios cover the platform, what's the coverage gap.
2. **Scenario library** — table per the scenario shape above. The headline artifact.
3. **Findings table** — flow, missing scenarios (which category), severity, fix.
4. **Severity** per rubric.
5. **Evidence** — references to code paths that need scenarios; existing test names that miss the case.
6. **Recommended fix** — specifically, "Add an integration test at `tests/proposal/sad-path.test.ts` covering scenario S-014." If automation isn't feasible, "Add to manual QA checklist with date."
7. **Implementation complexity** — `small` per scenario; `medium` for setting up test infrastructure that doesn't exist yet.
8. **Owner/surface affected** — varies by scenario.
9. **Follow-up questions** — about acceptable behavior in partial-failure paths.

# Example Prompt

> Generate the QUAY scenario library per `skills/quay/genius-team/institutional-qa-scenario-simulator/SKILL.md`. For each user-facing flow, produce happy / sad / edge / partial / race scenarios in the schema above. Identify gaps where automation is missing. Emit findings per `FINDINGS_SCHEMA.md` for flows with no scenario coverage. Do not write actual tests; produce specifications. Append to current audit board.

# Related Skills

- [lifecycle-state-machine-auditor](../lifecycle-state-machine-auditor/SKILL.md) — provides the states whose transitions become scenarios.
- [n8n-workflow-reliability-engineer](../n8n-workflow-reliability-engineer/SKILL.md) — partial-failure and race scenarios apply directly to workflows.
- [adversarial-operations-reviewer](../adversarial-operations-reviewer/SKILL.md) — abuse cases become scenarios.
- [enterprise-ux-psychologist](../enterprise-ux-psychologist/SKILL.md) — UI behavior during sad paths.
- [integration-contract-reviewer](../integration-contract-reviewer/SKILL.md) — contract violations as scenarios.
