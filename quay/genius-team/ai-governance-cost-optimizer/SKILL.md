---
name: quay-ai-governance-cost-optimizer
description: Governs QUAY's AI usage — token budget, model selection, caching, prompt versioning, hallucination containment, human-review gates, and runaway-cost prevention. Catches AI features that are expensive, ungated, or making decisions they shouldn't.
---

# Purpose

QUAY uses AI in several places: proposal drafting, transcript summarization, mentor-intro suggestion, intelligence notes, possibly weekly-sentiment analysis. Each is a feature, but also a cost line and a trust surface. Without governance, a single bug in an n8n loop can produce a four-figure bill overnight, and a single confidently-wrong AI summary can damage a founder relationship.

This skill produces an **AI action policy** for QUAY: per AI feature, what model, what budget, what prompt version, what gate, what failure behavior. It then audits the current implementation against the policy and finds the gaps.

# When to Use

- Every full audit and every `ai-cost` audit.
- Before adding a new AI feature.
- When the token bill rises faster than feature usage justifies.
- Before opening any AI-generated artifact to founders/clients (i.e., before AI output stops being "staff-only draft").
- When changing models (e.g., upgrading to a more expensive frontier model) — the budget math changes.

# Expected Inputs

1. List of AI calls in the codebase (any `anthropic.*`, `openai.*`, model-API calls).
2. Where those calls live — app routes, n8n nodes, Supabase functions, cron jobs.
3. The prompt(s) used.
4. The model(s) used.
5. Provider billing data, if available — at minimum, recent monthly trend.
6. Where AI output is stored (per `data-lifecycle-governor`).
7. Where AI output is shown to humans, and whether they review or auto-trust it.

# Required Context to Inspect

- `grep -rni "anthropic\|openai\|claude\|gpt-\|llm\|completion" --include='*.ts' --include='*.tsx' --include='*.js' --include='*.json'`
- n8n workflows for "AI" / "Anthropic" / "OpenAI" nodes.
- `skills/quay/ai-feature-implementation/SKILL.md` — declared AI conventions.
- Prompt files (typically `prompts/*.md` or inline strings).
- Provider dashboards if reachable — usage logs.

# Review Methodology

For every AI call site, produce the **AI action policy entry**:

```
feature: <name, e.g., "weekly_sentiment_summary">
trigger: <what kicks this off — survey close, manual, cron>
model: <which model>
expected_cost_per_call: <$0.0X based on token estimate>
expected_calls_per_period: <per day, per cohort, per founder>
expected_monthly_budget: <product of the above + buffer>
prompt_location: <file path>
prompt_version: <hash or version number>
caching_strategy: <none | prompt-cache | output-cache + TTL>
human_gate: <required | optional | none>
gate_rationale: <one sentence>
hallucination_containment: <citation required | grounded in source doc | none>
failure_behavior: <retry x N then drop, retry then DLQ, log and continue, surface error to user>
output_destination: <where the output is stored, who sees it>
confidence_threshold: <none | "below X, surface for human review">
```

Anything missing is a finding. Inconsistencies (e.g., a feature with `human_gate: none` but `output_destination` is founder-facing) are findings.

## Five governance pillars

1. **Cost discipline.** Every AI call has an estimated cost. Total monthly budget is named. Budget breach has an alert.
2. **Model right-sizing.** Cheap model where cheap is fine (classification, extraction, formatting). Expensive model only where reasoning is required. Default to the cheaper model and upgrade with evidence.
3. **Caching.** Repeated prompts cache. Long stable system prompts use provider prompt-caching. Repeated outputs (same summary requested twice) read from output cache before re-generating.
4. **Human gating.** AI drafts go to humans before reaching founders/clients. Exceptions are explicitly chosen, not accidental.
5. **Failure containment.** AI calls fail. Failures must not blackhole work or loop infinitely. Each call site has a defined failure path.

# Severity System

- **P0** — Any of:
  - An AI call can be triggered in a loop by a producer that fires on its own output (silent infinite bill).
  - AI output reaches an external user (founder, mentor, client) with no human gate **and** with high stakes (decisions, status, financial info, NDA-covered content).
  - Provider credentials are reachable from the client bundle.
  - There is no token budget cap on a workflow that can fire many calls per trigger.
- **P1** — No expected-cost model exists for an AI feature. Prompts are inline strings with no versioning. No caching despite repeated identical prompts. Failures retried indefinitely. AI output stored with no parent (orphan AI artifacts). Hallucination containment absent for a feature that produces founder-visible claims.
- **P2** — Model is over-sized for the task (using premium model for classification). Prompt drift across surfaces (same task, three slightly different prompts). No confidence threshold on outputs that influence prioritization. No audit log of AI calls.
- **P3** — Prompts have poor formatting, lack examples, or aren't kept under source control.

# Checklist

- [ ] Every AI call site catalogued, with the policy entry above filled in.
- [ ] A monthly AI budget is named and tracked.
- [ ] An alert fires before budget breach (handoff to `observability-telemetry-architect`).
- [ ] Each call site has a defined failure path; no infinite retries.
- [ ] Each call site has a model choice justified — cheaper model first, premium only with reason.
- [ ] Prompt-caching is on for any stable, long system prompt.
- [ ] Output caching exists for any repeatable computation (transcript-> summary, given same transcript hash).
- [ ] Prompts are versioned files, not inline strings. Each version has a created_at and a "what changed" note.
- [ ] AI output that reaches external users has a human gate, with one of three patterns: (a) staff approves before send, (b) human-edited before send, (c) explicitly marked AI-draft with no commitments.
- [ ] Hallucination containment: outputs that make factual claims cite their source (the transcript, the proposal text) or are explicitly framed as suggestions.
- [ ] No AI call is in the critical path of a request the user is waiting on (per `quay-n8n-boundaries` and `quay-ai-feature-implementation`).
- [ ] AI outputs are stored with a parent reference and inherit deletion.
- [ ] Token usage per call is logged (input tokens, output tokens, model). At minimum aggregable per feature.

# QUAY-Specific Questions

- **Proposal drafting**: who reviews the draft before it goes to a founder? Is the AI labeled, or does the founder see "from QUAY"?
- **Transcript summaries**: are these staff-only at first, or shared with founders / mentors? If shared, what's the gate?
- **Mentor-intro suggestions**: does staff review the suggestion before initiating the intro, or is the intro auto-sent? Auto-send is dangerous.
- **Intelligence / sentiment notes**: who reads these? If founders see sentiment summaries about themselves, that's a major UX/privacy concern (handoff to `enterprise-ux-psychologist`).
- **n8n + AI**: is there any n8n workflow that triggers on AI output (e.g., generates a summary, posts to Slack, the post triggers another flow that generates another summary)? Verify no cycle.
- **Model selection**: is staging using the same model as prod, or a cheaper one? If different, drift in behavior between environments.
- **Read.ai already provides summaries**: does QUAY's AI also summarize? If yes, why not use Read.ai's output and save the call? If QUAY's adds value, what's the differentiator?

# Common Failure Modes

- **The retry loop bill.** A flow retries on transient failure, but the failure is "rate-limited"; retries hit rate limit too, but the cost still accrues per attempt.
- **The fanout bill.** A daily cron generates a summary per founder × per cohort × per meeting. Numbers multiply silently. Three cohorts × 15 founders × 10 meetings/week × $0.05 = $22/week — fine, but tomorrow's spec change to "generate hourly" makes it $5,000/month.
- **Prompt drift.** Three places in the code do "summarize this transcript" with slightly different prompts and slightly different output shapes. Downstream consumers break randomly.
- **Hallucinated facts in founder-facing output.** "Your last meeting covered X, Y, Z" — X happened, Y didn't, Z is from a different meeting. Founder loses trust.
- **AI as decision-maker.** "Top mentor for this founder" is generated by AI and presented to the founder. The founder picks. The decision is now AI's, not staff's, and the staff can't intervene.
- **No deletion of AI artifacts.** Proposal deleted; summaries remain forever, sometimes containing now-irrelevant content.

# Anti-Patterns

- "We'll optimize cost later." Costs scale with usage; if the feature succeeds, cost outruns the team's attention.
- Inline prompts as string concatenations with user input — also a prompt-injection vector (handoff to `adversarial-operations-reviewer`).
- "The model is good enough that we can skip review." Good enough at the demo. Wrong on a long tail of edge cases.
- Adding more AI calls to fix bad AI output — generating a summary of the summary, an evaluator over the generator. Each layer multiplies cost; rarely improves trust.
- Using the same model everywhere because "it's simpler." Simpler ≠ cheaper; right-sizing matters.

# Output Format

1. **Executive summary** — one paragraph: does QUAY have AI governance, or are AI calls scattered?
2. **AI policy table** — one row per AI feature, with the entry above. This is the headline artifact for this skill.
3. **Monthly cost estimate** — based on token estimates × call frequency. Best-case / expected / worst-case (with the worst-case assuming a bug fires the call 10× more than expected).
4. **Findings table** — feature, gap, severity, fix.
5. **Severity** per rubric.
6. **Evidence** — file:line of each call site, prompt content (or a hash), recent usage logs.
7. **Recommended fix** — specific: move prompt to file, add cache, add gate, switch model, add budget alert.
8. **Implementation complexity** — `small` for adding a gate, version, or cache; `medium` for migrating prompts to versioned files; `large` for changing AI placement (e.g., moving an in-route AI call to an async queue).
9. **Owner/surface affected** — `ai`, plus the surface that triggers or consumes.
10. **Follow-up questions** — what monthly budget is acceptable; what features are willing to take a human-gate vs none.

# Example Prompt

> Audit QUAY's AI usage per `skills/quay/genius-team/ai-governance-cost-optimizer/SKILL.md`. Catalogue every AI call site across the codebase and n8n workflows. Produce the AI policy table with one row per feature. Estimate monthly cost. Identify all gaps (no gate, no cache, no budget, no failure path, no version control on prompts). Emit findings per `FINDINGS_SCHEMA.md`. Do not change any prompts or models. Append to current audit board.

# Related Skills

- [n8n-workflow-reliability-engineer](../n8n-workflow-reliability-engineer/SKILL.md) — most AI calls are in n8n; reliability and AI governance overlap.
- [data-lifecycle-governor](../data-lifecycle-governor/SKILL.md) — AI artifacts as a data class.
- [observability-telemetry-architect](../observability-telemetry-architect/SKILL.md) — AI usage metrics and cost alerts.
- [enterprise-ux-psychologist](../enterprise-ux-psychologist/SKILL.md) — how AI output is framed to maintain user trust.
- [platform-economics-analyst](../platform-economics-analyst/SKILL.md) — AI cost as a component of platform COGS.
- [adversarial-operations-reviewer](../adversarial-operations-reviewer/SKILL.md) — prompt injection and abuse of AI surfaces.
