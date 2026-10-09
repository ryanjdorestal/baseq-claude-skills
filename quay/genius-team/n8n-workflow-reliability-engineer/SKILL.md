---
name: quay-n8n-workflow-reliability-engineer
description: Audits QUAY's n8n workflows for idempotency, retry logic, dead-letter handling, schema drift, webhook signing, duplicate-event handling, and the gap between "test workflow URL" and "production workflow URL." Treats n8n as production infrastructure, not a wiring diagram.
---

# Purpose

n8n is QUAY's orchestration spine. Drive triggers, Read.ai webhooks, Slack events, scheduled jobs, AI summarizations — they all run there. n8n Cloud has constraints (no env vars in Code nodes, no exact-once delivery, limited observability) that make naive workflows fragile in ways that only show up at the worst time.

This skill audits every workflow against a reliability spec: triggers signed, payloads validated, idempotency keys respected, retries bounded, failures dead-lettered, executions observable, and test URLs not used in production.

# When to Use

- Every full audit, every `n8n-only` audit, every `pre-deploy` audit if n8n was touched.
- When a workflow misfires (duplicate row, missing event, infinite-retry incident).
- Before activating any new workflow in production.
- When migrating from n8n self-hosted to Cloud or vice versa.
- When n8n bills or execution counts spike unexpectedly.

# Expected Inputs

1. The list of active workflows (n8n UI export or `n8n/workflows/*.json` if checked into the repo).
2. Webhook URLs in use (and whether they're test or production URLs).
3. Credential names in n8n (without values).
4. Any error workflow configured.
5. Recent execution log samples — successes and failures.

# Required Context to Inspect

- `n8n/workflows/*.json` if available in the repo.
- The n8n project name(s) — production vs staging.
- `skills/quay/n8n-boundaries/SKILL.md` — the existing rules.
- The producer side for each webhook (Slack app event subscription, Read.ai webhook config, Drive watch, etc.) — what fires the trigger.
- Supabase RPCs called from n8n.

# Review Methodology

For every workflow, score against the **n8n reliability spec**:

| # | Concern | Pass criterion |
|---|---|---|
| 1 | Trigger URL | Production URL (not the "test" URL that requires the workflow to be in execute-mode). |
| 2 | Activation state | Active in production project. No "draft" workflows handling production events. |
| 3 | Auth / signature | Webhook validates signature (Slack signing secret, Read.ai HMAC, custom HMAC). No "trust the public URL" surfaces. |
| 4 | Schema validation | First-node validation of payload shape; reject 400 on shape mismatch, not 500. |
| 5 | Idempotency | Workflow checks an `idempotency_key` (from event ID, message ID, or a hash) before producing side effects. Re-running with the same key is a no-op. |
| 6 | Dedup window | If the producer can fire duplicates, the workflow tolerates them for the producer's known retry window. |
| 7 | Retry policy | Bounded retries with exponential backoff. No infinite retries. Retry count visible. |
| 8 | Dead-letter | After max retries, the event is recorded somewhere durable (`workflow_dead_letters` table or equivalent) with payload + error. |
| 9 | Side-effect ordering | If multiple side effects (Supabase write, Slack post, Drive copy), ordering and rollback semantics are explicit. |
| 10 | Code-node hygiene | No env vars relied on (n8n Cloud doesn't pass them); no >30-line Code nodes; no secrets inline. |
| 11 | Activity event | The workflow emits at least one activity event on success and one on failure (per `quay-activity-feed-model`). |
| 12 | Observability | Workflow has a label/tag and feeds into the operator dashboard (see `observability-telemetry-architect`). |
| 13 | Test isolation | Workflow does not write to production data when run from the n8n test runner. (Use feature-flagged paths or separate workflows for testing.) |

# Severity System

- **P0** — Any of:
  - Workflow accepts unsigned webhooks for high-impact events (creates founders, updates roles, posts to founder-visible channels).
  - Workflow has unbounded retry that can loop indefinitely.
  - A "test workflow URL" is referenced by a production producer (Slack app, Drive watcher, scheduler).
  - Workflow performs a side effect with no idempotency check on a producer known to retry (Slack retries 3x; Drive watches re-fire on tombstone changes; Read.ai may resend).
  - Workflow writes data with the service-role key bypassing RLS via raw SQL.
- **P1** — Webhook payload not schema-validated. No dead-letter for failed executions. Retry policy default (5x immediate retry — too aggressive). Side effects not ordered/transactional and a partial failure leaves the system inconsistent.
- **P2** — Workflow lacks an activity event on completion. Code node > 30 lines (per `quay-n8n-boundaries`). No tag for observability. Schema for the trigger lives only in the workflow, not in `schemas/`.
- **P3** — Workflow name uninformative. Variables named `data1`, `data2`. No description.

# Checklist

Per workflow:

- [ ] Production URL, not test URL, configured at the producer.
- [ ] Workflow is in **active** state on the production project.
- [ ] Signature/auth verified at trigger.
- [ ] Schema validation at first node; rejects invalid payloads with a 4xx.
- [ ] Idempotency key check before any write.
- [ ] Retries bounded (suggested: 3, exponential, max 5 min total).
- [ ] Dead-letter destination defined; payload + error stored.
- [ ] Side-effect ordering documented inside the workflow (a "Set" node at the top with a comment, or a docstring node).
- [ ] No env-var reliance in Code nodes.
- [ ] No secrets inline; use n8n credential references.
- [ ] Activity event emitted on terminal outcomes.
- [ ] Workflow tagged for observability (`production`, `cohort:*`, `surface:*`).
- [ ] Test execution does not write to production tables.

Per integration (Slack, Drive, Read.ai, Supabase):

- [ ] Producer-side configuration matches the production workflow URL.
- [ ] Producer-side retry behavior is known and documented.
- [ ] Credential is named and scoped (e.g., separate Slack tokens for different bots if any).
- [ ] Failure of the integration is visible (Slack alert channel, dashboard panel).

# QUAY-Specific Questions

- The **Drive trigger**: does it watch a specific folder, or the whole shared drive? Does it fire on file edits, on new files, or both? What stops it from firing on its own writes (loop)?
- The **Read.ai webhook**: does Read.ai sign its payloads? Are duplicates possible? What's the retry policy on their side?
- The **Slack event subscription**: Slack retries 3× over ~5 minutes if you don't 200 quickly. Does the workflow reply fast (within 3s) and queue the actual work, or does it do the work inline and time out?
- The **proposal-submit flow**: when a founder submits a proposal via Slack, what writes? Supabase row, Slack notification to staff, possibly an AI draft generation. Is this transactional or best-effort? What if the Slack post fails after the row is written?
- The **transcript ingestion**: Drive new file → parse → AI summary → Supabase row → Slack post. If AI summary fails, do we have the raw transcript stored? If Slack post fails after Supabase write, do staff know?
- The **weekly sentiment survey**: scheduled flow that DMs founders. If a founder is offboarded mid-week, do they still receive the DM? (Should not.)
- The **event receiver / canonical event ingest**: per `N8N_EVENT_CONTRACTS`-style docs (if any exist), is there one workflow that all events flow through, or many siloed workflows? Either is fine, but the answer must be deliberate.

# Common Failure Modes

- **The test-URL trap.** Slack app is pointed at the workflow's test URL. It works while you're staring at n8n with "Execute Workflow" on. The moment you close the tab, Slack events are lost — but the workflow looks fine.
- **The retry storm.** A downstream API (Anthropic, Supabase) returns 5xx briefly. n8n retries immediately 5×, costing $X. Then the production fires for 100 events at once; the storm compounds.
- **The duplicate event silent-double.** Drive watches re-fire when files are restored from trash. The workflow ingests the same transcript twice and now there are two summary rows. Dashboards show whichever's newest.
- **The partial write.** Workflow inserts a row, then posts to Slack. Slack post fails. The row exists but no one knows to act on it. No alert. Founders see weird state.
- **The env-var assumption.** Code node uses `process.env.SUPABASE_URL`. Locally fine; n8n Cloud doesn't pass it. Fails silently. Discovered when ingest stops working three weeks later.
- **The Code-node-as-application.** A 200-line Code node implements business logic. Untestable, unversioned, invisible to typecheckers. When it breaks, no one can read it.
- **The "I activated it once and forgot." workflow.** A workflow from three months ago is still active and writing to production. No one knows what it does.

# Anti-Patterns

- "We'll add idempotency later." You won't, and your duplicates are already in production data.
- "We don't need a dead-letter table; n8n has execution history." n8n Cloud history rolls; after the retention window, the event is gone.
- "Just disable the workflow when it's failing." If you disable, events queue up at the producer (or get dropped). Disabling is not a fix.
- "The signature check is fine — only Slack knows the URL." Webhook URLs leak. Signing is the protection.
- "We'll fix the retry storm by lowering the retry count to 1." Now transient failures lose events permanently. The right fix is exponential backoff with a cap.

# Output Format

1. **Executive summary** — one paragraph: how many workflows are in n8n, how many pass the reliability spec, what's the worst gap.
2. **Per-workflow scorecard** — workflow name, the 13-criterion checklist with pass/fail, severity of worst miss.
3. **Findings table** — workflow, gap, severity, fix.
4. **Severity** per rubric.
5. **Evidence** — workflow ID/name, node name, payload sample (sanitized).
6. **Recommended fix** — specific node-level change: "Add a Function node before the Supabase Insert that hashes (event_id, type) into idempotency_key and queries against `workflow_idempotency` table."
7. **Implementation complexity** — usually `small` per criterion, but `medium`/`large` if the workflow needs structural rework.
8. **Owner/surface affected** — `n8n` plus the consuming surface.
9. **Follow-up questions** — about producer retry behavior, acceptable retry budget, where dead-letters should land.

# Example Prompt

> Audit every active QUAY n8n workflow per `skills/quay/genius-team/n8n-workflow-reliability-engineer/SKILL.md`. Produce a per-workflow scorecard against the 13-criterion reliability spec. Emit findings per `FINDINGS_SCHEMA.md` for every miss. Cite workflow name and node. Do not edit any workflow. Append to current audit board.

# Related Skills

- [integration-contract-reviewer](../integration-contract-reviewer/SKILL.md) — schemas at every boundary; the producer side of webhook contracts.
- [observability-telemetry-architect](../observability-telemetry-architect/SKILL.md) — surfacing workflow failures to operators.
- [data-lifecycle-governor](../data-lifecycle-governor/SKILL.md) — where workflow side effects write.
- [ai-governance-cost-optimizer](../ai-governance-cost-optimizer/SKILL.md) — workflows that fire AI calls.
- [security-privacy-compliance-reviewer](../security-privacy-compliance-reviewer/SKILL.md) — credentials, signing, secret handling.
