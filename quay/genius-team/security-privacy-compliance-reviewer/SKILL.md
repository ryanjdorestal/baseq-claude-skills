---
name: quay-security-privacy-compliance-reviewer
description: Audits QUAY for PII handling, secret management, service-account scope, log hygiene, transcript sensitivity, NDA/private-meeting handling, least-privilege posture, and auditability. Catches the things that turn into legal/relationship incidents.
---

# Purpose

QUAY handles meaningful private data: founder identities, mentor introductions and feedback, meeting transcripts (often confidential), proposals (often containing IP or NDA-covered material), staff communications. Today's posture is "we're not Fortune 500" — but the *types* of data QUAY holds demand institutional treatment regardless of QUAY's headcount.

This skill audits secrets, service accounts, PII, transcripts, logs, and audit trails against a least-privilege, defense-in-depth baseline.

# When to Use

- Every full audit, every `auth-security` audit.
- Before any client institution onboards.
- Before exposing any new external surface (webhook, public form, oauth integration).
- After any near-miss (credential rotation, accidental share, etc.).
- At regular cadence (monthly minimum) — privacy debt accumulates silently.

# Expected Inputs

1. Secret inventory: where every credential lives (vault, env file, n8n credential, Google secret manager, etc.).
2. Service account list: every Google/Slack/Supabase service identity and what it can do.
3. The data sensitivity classification from `data-lifecycle-governor`.
4. Log destinations (Vercel logs, Supabase logs, n8n logs, Slack audit, etc.).

# Required Context to Inspect

- `.env.example` (never the real `.env`).
- Vercel env var list (names only).
- Supabase project settings — JWT secret, anon key, service-role key locations.
- Google Cloud / Workspace service account list.
- n8n credentials (names).
- Slack app credentials (signing secret, bot token holders).
- Any `*.json` in the repo that could be a credential (search `private_key_id`, `client_email`, `BEGIN PRIVATE KEY`).
- Log redaction config if any.
- `skills/quay/deploy-push-checklist/SKILL.md`.

# Review Methodology

Walk the audit through five domains.

## 1. Secrets

- **Inventory**: every secret has a known home.
- **Where it's stored**: Vercel env, GCP Secret Manager, n8n credential store, Supabase dashboard, password manager? One place per secret.
- **Where it's used**: which surface reads it. Service-role key should be in exactly two places (server runtime + n8n).
- **Rotation**: when was each rotated last? Is there a documented rotation procedure?
- **Exposure surfaces**: any secret in logs (search log samples), any secret in error messages, any secret in client-bundled JS, any secret in git history.

## 2. Service accounts

For each service account / bot token / API key:
- What scope does it have?
- Is it scoped to the **minimum** required (e.g., Drive service account scoped to one folder, not the whole workspace)?
- Who owns it (a person)?
- What's the rotation cadence?
- Is its activity logged?

QUAY-specific service identities:
- Google Workspace service account (for Drive, Sheets, etc.).
- Supabase service-role key.
- Slack app bot token + signing secret.
- AI provider keys (Anthropic / OpenAI).
- Read.ai integration credentials.
- n8n internal credentials (each named credential).

## 3. PII

QUAY PII includes:
- Founder names, emails, phone numbers.
- Mentor names, emails, professional history.
- Meeting transcripts (which can include personal stories, financial detail, legal matter).
- Proposal contents (often confidential strategy / IP).

For each PII type:
- Where is it stored?
- Who can read it?
- Is it transmitted to third parties (e.g., AI providers for summarization)? Under what contract?
- Is it deletable on request?
- Is it logged anywhere (logs are PII repositories no one thinks about)?

## 4. Transcripts & NDA-covered content

A specific concern because transcripts:
- Originate from meetings whose participants didn't necessarily consent to AI processing.
- Often contain sensitive content (financial, legal, personal).
- Are processed by external AI services.

Audit:
- Is there a meeting-level "private" or "skip" flag respected by ingestion?
- Are transcripts marked NDA / confidential surfaced differently in the UI?
- Are participants notified that transcripts are AI-summarized and stored?
- Is there a deletion path for a specific meeting on request?
- When a transcript fails the sensitivity policy (e.g., mentioned an unrelated client), what happens?

## 5. Logs & audit trail

- Application logs: do they contain PII? Tokens? Secrets?
- Database query logs: same.
- AI provider logs: what's sent in the prompt is logged on their side; review their data-handling agreement.
- Slack audit log: does QUAY retain it?
- Audit log of role changes, logins, impersonations: exists, retained, reviewable.

# Severity System

- **P0** — Any of:
  - A credential in the repo (current or historical), in `NEXT_PUBLIC_*`, in client-bundled JS, or in logs without redaction.
  - A service account with scope wildly exceeding need (e.g., Drive service account with workspace-admin).
  - PII in logs that are publicly accessible or sent to a third party without DPA.
  - Transcript content reaching a third party AI provider without an explicit user-consent/contract path.
  - No path to delete a specific user's data (GDPR-style erasure request would fail).
- **P1** — Secret rotation has never happened or has no procedure. Service-account ownership unclear (no human attached). Audit log absent for role changes / data exports. Sensitive content (transcripts) handled the same as non-sensitive.
- **P2** — Logs contain PII but aren't transmitted externally. Secrets in two places (slight risk of drift). NDA-content not labeled in UI.
- **P3** — Documentation gaps: secret-rotation runbook missing, sensitivity classification not explicit on every object type.

# Checklist

- [ ] Secret inventory exists with: name, location, used-by, owner, last-rotated, rotation-procedure.
- [ ] No secret in source control. Verified via `git log -p | grep -E '(SUPABASE_SERVICE|sk-|xoxb-|-----BEGIN)'`.
- [ ] No secret in `NEXT_PUBLIC_*`.
- [ ] No secret in built JS (verify by inspecting the deployed bundle, not just source).
- [ ] Service-role key reachable only by server runtime and n8n; never by client; not in any log.
- [ ] Service account JSON files: not in the repo; stored in a managed secret; rotation documented.
- [ ] Each service account has a human owner.
- [ ] PII inventory exists; transmission to third parties documented.
- [ ] Transcript sensitivity policy documented; private-meeting opt-out respected.
- [ ] Audit log of: logins, role changes, impersonations, bulk exports, secret access (where supported).
- [ ] GDPR-style erasure runbook exists, even if unused.
- [ ] Logs sanitized (no tokens, no full emails in production logs).
- [ ] AI provider DPA reviewed; data retention with provider known and acceptable.
- [ ] Slack signing secret verified on every webhook.
- [ ] Drive folder permissions: no "anyone with link" on confidential folders.

# QUAY-Specific Questions

- Where is the Google service account JSON for QUAY's Drive/Sheets integration? In the repo? In a `.gitignore`'d file? In Vercel env? (Required: GCP Secret Manager or env var with the JSON contents inlined, never a file in the repo.)
- Are Supabase service-role keys distinct between staging and prod? (Required: separate Supabase projects.)
- Is the Read.ai webhook signed and verified at the n8n trigger?
- When AI summarizes a transcript, is the full transcript content sent to the AI provider? Have you reviewed the provider's data-retention terms for that content?
- Does QUAY have a Data Processing Agreement with Anthropic / OpenAI / Read.ai?
- For private/sensitive meetings (mentor 1:1 feedback, founder personal struggles): is there a mechanism to mark them "do not summarize" or "do not share with founder"?
- Where are old transcripts archived? Drive? Indefinitely? Is there a retention policy?
- If a founder asks "delete all my data" tomorrow, what's the actual procedure? How many places does it touch?
- Has the staff Google Workspace been hardened (MFA required, no personal accounts as admins)?
- Is the Slack workspace set to private / invitation-only? Are external organizations / shared channels in play?

# Common Failure Modes

- **The committed credential.** `service-account.json` accidentally checked in once, removed, but still in git history. Repo cloned widely; the credential is effectively public until rotated.
- **The wildcard scope.** Google service account given `https://www.googleapis.com/auth/drive` instead of `drive.file`. Now has access to every file the impersonation target can see.
- **The PII-in-logs problem.** Logging `console.log("Processing user", user)` where `user` includes email, name, sometimes more. Logs forwarded to a third party SaaS. PII now on someone else's servers.
- **The "shared with everyone" Drive doc.** A staff member shares a doc with link-only access to send to a founder; the founder forwards to a mentor; the link is now in 4 inboxes.
- **The transcript that shouldn't have been summarized.** A founder discussed personal mental health in a check-in meeting. The transcript was auto-summarized, the summary appeared in the cohort feed. Trust damaged irreversibly.
- **The token in the bundle.** A "private" API key marked `NEXT_PUBLIC_` for "convenience" ships to every browser.
- **The rotation that didn't happen on offboarding.** A staff member left; their service account stayed; their personal tokens stayed in n8n credentials.

# Anti-Patterns

- "Only staff has access to that." Until the access is reviewed monthly, you don't know.
- "We're too small for compliance to matter." The data types matter, not the team size.
- "We'll rotate when we get hacked." You won't know you've been hacked if you don't audit.
- Putting service account JSONs in shared Google Drive folders for "team convenience."
- Treating any "private" link as actually private.

# Output Format

1. **Executive summary** — one paragraph: secrets/PII/transcript posture; top three risks.
2. **Secret inventory table** — name, location, used-by, owner, last-rotated.
3. **Service account scope review** — account, scope today, scope minimum, gap.
4. **PII flow map** — type, source, storage, third-party transmission, retention.
5. **Findings table** — concern, severity, fix.
6. **Severity** per rubric.
7. **Evidence** — file:line, config screenshot description, log sample (redacted).
8. **Recommended fix** — specific: rotate this key, narrow this scope, move this secret, add this redactor.
9. **Implementation complexity** — `small` to `medium`; `large` for migrating a credential store.
10. **Owner/surface affected** — `security-privacy`, plus the surface using the credential.
11. **Follow-up questions** — about compliance posture (GDPR, SOC 2 desire, etc.) and what's NDA in current cohorts.

# Example Prompt

> Audit QUAY's security and privacy posture per `skills/quay/genius-team/security-privacy-compliance-reviewer/SKILL.md`. Build the secret inventory, service-account scope review, and PII flow map. Identify any credential in code/logs/bundle. Identify any service account with wildcard scope. Identify any path where transcript or proposal content reaches a third party without explicit contract. Emit findings per `FINDINGS_SCHEMA.md`. Do not rotate keys or change configs. Append to current audit board. If you find an exposed credential, STOP THE AUDIT and emit the emergency notice per ORCHESTRATION.md.

# Related Skills

- [auth-identity-architect](../auth-identity-architect/SKILL.md) — credentials in auth flows.
- [multi-tenant-boundary-architect](../multi-tenant-boundary-architect/SKILL.md) — Drive and Supabase permission scopes.
- [data-lifecycle-governor](../data-lifecycle-governor/SKILL.md) — retention and deletion semantics.
- [adversarial-operations-reviewer](../adversarial-operations-reviewer/SKILL.md) — abuse cases that exploit weak privacy.
- [observability-telemetry-architect](../observability-telemetry-architect/SKILL.md) — audit log surfacing.
