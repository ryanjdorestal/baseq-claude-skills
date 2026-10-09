---
name: quay-ai-feature-implementation
description: Add an AI-powered feature to QUAY safely. Covers model selection, prompt versioning, caching, tool use, evaluation, and the boundary between AI and the rest of the system.
---

# QUAY AI-Assisted Feature Implementation

## Purpose

Add an AI feature to QUAY in a way that is reviewable, debuggable, and reversible. AI is a capability, not a strategy — every model call has a defined input, a defined output, a defined failure mode, and a way to evaluate whether it's actually helping.

## When to use

- Adding any feature that calls an LLM (summarization, classification, drafting, routing).
- Replacing a heuristic or human step with an AI step.
- Introducing tool use, structured outputs, or multi-step agents.
- Reviewing AI-generated content destined for a member-facing surface.

Do **not** use it for fully scripted logic that incidentally looks "AI-ish" (rule-based classifiers, regex extractors).

## Expected inputs

1. **Job to be done** — one sentence: what does the AI step decide or produce?
2. **Input contract** — exact shape of what goes in (schema-validated).
3. **Output contract** — exact shape of what comes out (structured if possible).
4. **Latency budget** — synchronous (< 2s), background (seconds), or batch (minutes).
5. **Audience** — staff-only, member-facing (with label), or system-only.
6. **Fallback** — what happens when the model errors, times out, or returns garbage.

## Output format

For each AI feature:

1. **Prompt file** at `prompts/<feature>.v<N>.md` with frontmatter: model id, version, owner, last-evaluated date.
2. **Caller** at `lib/ai/<feature>.ts` — single function with typed input/output, prompt-cache key, fallback path.
3. **Schemas** — Zod for input + output (structured output validated; free-text outputs still validated for length and toxicity flags).
4. **Eval set** at `evals/<feature>/cases.json` — at least 10 cases with expected behavior.
5. **Wiring** — call site (app route, n8n node), with `activity_event` of type `ai.summary_generated` (or appropriate) emitted.

## Defaults for QUAY

- **Models:** Claude Opus 4.7 for staff-facing reasoning, Claude Sonnet 4.6 for portal-facing summaries, Claude Haiku 4.5 for high-volume classification. Override only with a documented reason.
- **Prompt caching:** on by default. The cache key is the prompt version + the stable input prefix; per-request data goes in the suffix.
- **Structured output** is the default. Free text only when the audience actually needs prose.
- **System prompt + user prompt are versioned together** in the prompt file. No string-concatenation in the caller.
- **No retries with re-prompting** on a failed structured-output validation more than once. After one repair attempt, fall back.

## Constraints

- AI never bypasses RLS. The AI layer is a consumer of the same data surfaces as a human user.
- AI output that lands in a member-facing surface is labeled (`AI-generated • <date>`) and links to its sources.
- No model call inside a Supabase trigger or a hot request handler with no async path.
- API keys live only in server-side env. Never shipped to the browser.
- Every AI feature has at least one eval case representing a known failure mode (adversarial input, empty input, ambiguous input).
- Prompts are versioned in git. No prompt edits in production without a PR.

## Anti-patterns

- "Let's just ask the model" without an output schema.
- An AI feature with no eval set — there's no way to detect regressions.
- Caching turned off because "it might give stale answers" — caching the *prompt prefix* is not caching the *answer*.
- Calling the model from three different places with three slightly different prompts.
- AI-generated content that appears member-facing without a label.
- Synchronous AI call in a path that already has a Supabase round-trip and a Slack post — that's a queue job.

## Checklist

- [ ] Job statement, input contract, output contract, latency budget, audience, fallback documented.
- [ ] Prompt file versioned with frontmatter (model id, version, owner, last-evaluated date).
- [ ] Caller is a single typed function with one prompt source.
- [ ] Zod schemas for input + output.
- [ ] Prompt caching enabled with a stable prefix.
- [ ] At least one repair attempt on structured-output validation failure, then fallback.
- [ ] Eval set of ≥ 10 cases, includes adversarial / empty / ambiguous.
- [ ] `activity_event` emitted on each generation.
- [ ] Member-facing output is labeled and linked to sources.
- [ ] No API key reachable from the browser.

## Example prompt

> Implement a `summarize_mentor_session` AI feature per `skills/quay/ai-feature-implementation/SKILL.md`. Input: Read.ai transcript + member + mentor. Output: structured summary (topics, action items, follow-up). Audience: staff-facing first, member-facing in v2. Latency budget: background. Model: Sonnet 4.6 default. Produce prompt file, caller signature, schemas, eval cases. Do not commit or deploy.
