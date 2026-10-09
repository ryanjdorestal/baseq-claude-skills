# Reference Frameworks

Public, freely-accessible references that shaped the Genius-Team skills. Use these for principles and vocabulary; do not copy copyrighted content verbatim into skill files.

**Web access status during authoring:** the Claude Code session that created this folder did not perform live web fetches. References below are summaries of widely-known frameworks recalled from training; verify and link to official sources before quoting in audit output.

## Repo-local prior art used

These existing QUAY skill files were inspected and informed the Genius-Team layer:

- `skills/quay/README.md` — QUAY vocabulary (member, mentor, cohort, staff, activity, workflow, surface, portal) and hard rules.
- `skills/quay/architecture-review/SKILL.md` — the QUAY "spine" and existing finding format.
- `skills/quay/n8n-boundaries/SKILL.md` — orchestration boundary, idempotency requirements, contract rules.
- `skills/quay/supabase-schema/SKILL.md` (referenced) — RLS-on-by-default policy.
- `skills/quay/activity-feed-model/SKILL.md` (referenced) — unified event model.
- `skills/quay/ai-feature-implementation/SKILL.md` (referenced) — AI call placement.
- `skills/quay/deploy-push-checklist/SKILL.md` (referenced) — pre-deploy gates.

The Genius-Team layer pressure-tests the assumptions in these files. Where it disagrees, the Genius-Team skill names the conflict and proposes a resolution; it does not silently override.

## Authentication & identity

- **OWASP Authentication Cheat Sheet** — owasp.org. Authoritative checklist for session management, credential storage, MFA, password policy. Used as backbone for `auth-identity-architect`.
- **OWASP Session Management Cheat Sheet** — session id generation, timeout, fixation, rotation on privilege change.
- **NIST SP 800-63B** — Digital Identity Guidelines, especially AAL (Authentication Assurance Levels). For QUAY: staff = AAL2 with Google SSO; founder = AAL1 via magic link is acceptable initially but requires lifecycle controls.
- **Supabase Auth & RLS docs** — supabase.com/docs/guides/auth and /guides/database/postgres/row-level-security. Used as the source-of-truth for RLS patterns in `multi-tenant-boundary-architect` and `auth-identity-architect`.
- **Google Cloud IAM best practices** — cloud.google.com/iam/docs/using-iam-securely. Used for service-account discipline in `security-privacy-compliance-reviewer`.

## Multi-tenancy & boundaries

- **Public guidance on multi-tenant SaaS patterns** — broadly: pool vs. silo vs. bridge tenancy models. QUAY today is "pool with RLS"; the audit must verify RLS is the actual enforcement, not UI hiding.
- **Supabase RLS examples** — for cohort/org/role-scoped policies.
- **Postgres docs on row security** — postgresql.org/docs. The base layer beneath Supabase RLS.

## Data lifecycle & governance

- **NIST SP 800-88 Rev. 1** — Guidelines for Media Sanitization. Used for the "what does delete mean" question in `data-lifecycle-governor`.
- **Public CDC/healthcare privacy patterns** (for sensitivity classification vocabulary — not because QUAY handles PHI, but because the public-domain classification scheme is useful).
- **GDPR public summaries** — right to erasure, data minimization, purpose limitation. QUAY isn't necessarily GDPR-bound today but founders and mentors include EU contacts; principles still apply.
- **Open-source patterns for event sourcing & CDC** — used in `data-lifecycle-governor` for canonical-source-vs-cache reasoning.

## AI governance

- **Anthropic responsible scaling policy** — public — used for hallucination containment and human-gate principles in `ai-governance-cost-optimizer`.
- **OpenAI model usage policies** (public docs) — referenced for prompt-injection failure modes.
- **NIST AI Risk Management Framework (AI RMF 1.0)** — for the "govern → map → measure → manage" structure applied to AI features.
- **Public writing on agentic cost governance** — token-bucket per workflow, model selection by stake, cache hits as first-class metric.

## Workflow reliability (n8n)

- **n8n docs** — docs.n8n.io. Especially execution data, error workflows, queue mode, credentials. Used in `n8n-workflow-reliability-engineer`.
- **AWS / GCP queue & DLQ patterns** — public architecture docs. Used for idempotency keys, dedup windows, at-least-once vs exactly-once semantics.
- **Google SRE Book — Chapter on incident response** — public on sre.google/books. Used for the incident vocabulary in `observability-telemetry-architect`.
- **Stripe-style API design guides** (publicly published blog posts, e.g. by Stripe engineering) — for idempotency-key and webhook signing patterns in `integration-contract-reviewer`.

## Observability & SRE

- **Google SRE Book and SRE Workbook** — sre.google. Used for SLI/SLO reasoning, alerting on user pain, four golden signals.
- **OpenTelemetry docs** — opentelemetry.io. Used for distributed tracing vocabulary even if QUAY isn't running OTel today.
- **Public Honeycomb engineering posts** on observability — cardinality, trace-centric debugging.

## Product & PM

- **Marty Cagan's "Inspired" (public summaries)** — outcomes vs outputs framing. Do not include verbatim text.
- **Public Linear / Notion / GitLab handbooks** — for product operations vocabulary and bug-triage rituals.
- **Public ICE / RICE / WSJF prioritization frameworks** — for `product-scope-ruthless-prioritizer` severity-to-priority conversion.
- **Public Jobs-To-Be-Done (Clayton Christensen lineage) summaries** — for `enterprise-ux-psychologist` user-job framing.

## QA & adversarial

- **OWASP Top 10** — owasp.org. Especially A01 Broken Access Control and A03 Injection — used in `adversarial-operations-reviewer`.
- **OWASP API Security Top 10** — applicable to n8n webhooks and Supabase RPCs.
- **Public Atlassian / GitLab incident review templates** — for the "what could go wrong" framing in `institutional-qa-scenario-simulator`.

## Slack platform

- **Slack platform docs** — api.slack.com. Used for event signing, app-level vs bot tokens, rate limits, and surface considerations in `integration-contract-reviewer` and `adversarial-operations-reviewer`.

## Google Workspace integration

- **Google Drive API docs** — developers.google.com/drive. Used for permission model, shared drives vs my drive, service account impersonation considerations in `security-privacy-compliance-reviewer`.
- **Google Workspace audit logs** — for `observability-telemetry-architect`.

## Platform economics

- **Public cloud pricing pages** — Vercel, Supabase, Anthropic, OpenAI, n8n Cloud. Used as inputs to `platform-economics-analyst` cost models.
- **Public engineering blog posts** on per-tenant cost attribution — for cohort-level COGS reasoning.

---

## How to use this file

When a Genius-Team skill produces a finding that leans on outside principles (e.g., "this RLS policy is missing the kind of scope check NIST 800-63B expects for AAL2 sessions"), it should cite the framework in the finding body. Do not paste copyrighted text. Link or name; explain the principle in your own words.

If a future audit session adds new references, add them here. If a reference goes stale or is no longer authoritative, mark it deprecated rather than deleting (so audit findings that referenced it remain traceable).

## Anti-patterns

- **Citing a framework to inflate severity.** "OWASP says this is bad, so P0." No — the rubric in `FINDINGS_SCHEMA.md` is the only severity source. Frameworks justify the *finding*, not the *severity*.
- **Copying copyrighted material.** Summarize and link. Do not paste.
- **Citing a framework you didn't read.** If you don't know what NIST 800-63B says about AAL3, don't cite it — name the *principle* you're applying and leave the citation off until verified.
- **Cargo-culting enterprise patterns.** QUAY is not a Fortune-500 platform. A pattern designed for 10,000 tenants is wrong for QUAY's 3 cohorts. Adapt scale; don't import overhead.
