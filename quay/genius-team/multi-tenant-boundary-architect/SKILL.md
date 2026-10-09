---
name: quay-multi-tenant-boundary-architect
description: Verifies that QUAY's tenant, cohort, and role boundaries are enforced at the database (RLS) and not by UI hiding or trust. Catches cross-tenant leakage, over-permissioned service accounts, and the staff/founder/mentor/client visibility model.
---

# Purpose

QUAY OS is multi-tenant in three overlapping ways:
1. **Client institutions** that run accelerators on QUAY (future, but plan for it).
2. **Cohorts** within a client — a time-boxed group of founders.
3. **Roles** within all of the above — staff, founder, mentor, client-admin.

If these boundaries are enforced by "the UI doesn't show that button," QUAY is one curl command away from a public incident. This skill verifies enforcement at the data layer — Supabase RLS, Drive permissions, n8n credential scope, service-account least privilege — and produces findings wherever the enforcement is missing or weaker than the UI suggests.

# When to Use

- Before any client institution other than QUAY itself begins using the platform.
- Before publishing the founder-facing portal externally (i.e., before founders log in directly).
- When adding any cross-tenant feature (mentor sharing across clients, leaderboards, cohort-to-cohort references).
- During every `auth-security` and `handoff` audit.
- Whenever a new table is added to Supabase.

# Expected Inputs

1. Supabase schema and all RLS policies.
2. Supabase RPC definitions (these can be authorization escapes if they `SECURITY DEFINER` and skip RLS).
3. The role model from `auth-identity-architect`.
4. Drive folder structure and sharing rules (`drive` surface).
5. n8n credentials and which workflows use which.
6. Slack workspace/channel structure (especially private vs public channels, channel-per-cohort patterns).

# Required Context to Inspect

- `supabase/migrations/*.sql` — every `CREATE TABLE` and every `CREATE POLICY`.
- `supabase/functions/*` and any RPC declared via SQL functions.
- The Supabase JS client initialization in the portal — is it using the anon key + user JWT, or the service-role key?
- n8n credential list (names only, not values).
- Drive folder hierarchy (as observable from staff Drive).
- Slack channel naming and membership rules.

# Review Methodology

The audit walks four boundaries, in order of blast radius.

## 1. Client/org boundary

(If only one client exists today — QUAY itself — declare that explicitly and move on. But design the boundary model as if N clients existed, because adding it later is expensive.)

- Is there an `org_id` (or `client_id`) column on every row that conceptually belongs to a client?
- Does RLS scope by `org_id`?
- Is there any data **shared across orgs** by design (e.g., a global mentor pool)? If so, is that shared data ever joined with org-scoped data in a way that leaks org membership?
- Are Drive folders per-org? Is staff Drive the parent of client Drives, or are they siloed?

## 2. Cohort boundary

- Founders see only their cohort's data — is this RLS-enforced on every relevant table (tasks, proposals, intros, transcripts, activity events)?
- Mentors who serve multiple cohorts — is their view filtered, or do they see all cohorts they touch? What's the policy?
- A founder from Cohort 2 looking up a founder from Cohort 3 — should they see anything? (Probably: name + cohort, nothing else. Verify.)
- Are Drive cohort folders shared with only that cohort's founders? Test: log into Drive as a founder; can they navigate up?

## 3. Role boundary (staff vs founder vs mentor vs client-admin)

- Staff see everything (within their org). Verify by checking that staff RLS policies bypass cohort/role scopes via a role claim.
- Founders see their own cohort, their own data, mentor profiles they're introduced to, and that's it.
- Mentors see their assigned founders/cohorts and their own profile. They do NOT see other mentors' performance data, other cohorts' confidential info, or proposal contents (unless the proposal is being sent to them).
- Client-admins (future) see their client's data but not other clients'.
- For each role × table combination, there is a defined visibility (`full | scoped | none`). The audit produces this matrix and finds the gaps.

## 4. Staff-preview vs founder-view

Staff often need to **see what a founder sees** (for support). The audit checks:
- Is there a "view as founder" feature? If so, is it gated to staff, audited, and time-limited?
- Does the staff-as-founder view actually filter as the founder would, or just hide buttons?
- Is there any data that staff routinely access **about** a founder that the founder cannot see about themselves (e.g., internal notes)? Document this; it's normal but must be explicit.

## 5. Service-account / system scope

- Does n8n hold one service-role key, or multiple credentials with narrower scopes?
- Does the service account that touches Drive have org-wide access or scoped access?
- Are there any backend operations performed "as a user" via that user's JWT? If yes, where does the JWT come from and is its scope appropriate?

# Severity System

- **P0** — Any of:
  - A founder can query (via the JS client or any reachable API) data belonging to another cohort, org, or founder.
  - A table containing user-visible data lacks RLS.
  - A SECURITY DEFINER RPC bypasses RLS and is callable by non-staff with arbitrary parameters.
  - A Drive folder containing one cohort's confidential data is shared at the org level or with all founders.
  - The service-role key is reachable from a client bundle.
- **P1** — RLS exists but is overly permissive (e.g., `auth.role() = 'authenticated'` instead of a real scope). Staff-as-founder view is just UI hiding. Mentor cross-cohort visibility is undefined. Slack channels per cohort are public to the workspace when they should be private.
- **P2** — Audit log of cross-tenant access doesn't exist. RLS performance not indexed. Some tables have RLS but related views/materialized views don't inherit.
- **P3** — Inconsistent column naming (`org_id` vs `client_id` vs `tenant_id`). Slack channel naming inconsistent across cohorts.

# Checklist

- [ ] Every table has RLS enabled. (`SELECT * FROM pg_tables WHERE schemaname='public'` with `rowsecurity = true`.)
- [ ] Every table has at least one SELECT policy. (RLS enabled with no policies = nothing visible — sometimes correct, sometimes a bug; verify intent.)
- [ ] Every table has appropriate INSERT, UPDATE, DELETE policies. "No policy" defaults to "deny," which is correct, but every mutation path must be intentional.
- [ ] RLS policies use stable, non-user-editable inputs (`auth.uid()`, custom JWT claims) — not `user_metadata`.
- [ ] No SECURITY DEFINER function performs an action a non-staff user couldn't already perform via RLS-respecting paths, unless the function explicitly checks role at entry.
- [ ] Service-role key is held only by the server (and n8n credential store), never in `NEXT_PUBLIC_*`, never in client bundles.
- [ ] Role-based RLS exemptions (for staff) use a JWT custom claim, not a profile-table lookup that itself has RLS that staff must bypass.
- [ ] Drive folder permissions match Supabase scope: cohort folder is shared with cohort founders + staff, not the whole workspace.
- [ ] Slack channels per cohort are private; channel membership matches cohort membership and is updated on lifecycle events.
- [ ] A penetration test exists or is scheduled: log in as Founder A, attempt to read Founder B's data. Result documented.
- [ ] Cross-tenant tables (e.g., global mentor pool) have a clear "what's visible to whom" matrix.

# QUAY-Specific Questions

- Is there a single "QUAY org" today, with cohorts inside it? If yes, the org-scoping is latent — design it now and migrate later, or admit it's missing.
- The mentor pool: do mentors belong to a cohort, an org, or are they global across orgs? (If global, can a mentor's notes be seen across orgs? Probably no.)
- The activity feed: does it carry an `org_id`? `cohort_id`? Without these, RLS on the feed is impossible.
- Read.ai transcripts: which Drive folder do they land in? If "shared with everyone for now," that's likely P0.
- The Base44 clone: does it have its own tenancy model baked in? Does QUAY's model override it cleanly?
- Slack DMs vs channels: is sensitive data (proposal feedback, mentor decisions) DM'd, or posted in channels? DMs are not auditable in the same way; this is a boundary question.

# Common Failure Modes

- **"RLS on, no policies."** Table is invisible to everyone, including the app, so the app uses the service-role key everywhere. Defeats RLS.
- **`auth.role() = 'authenticated'` as the policy.** Any logged-in user passes — defeats tenancy entirely.
- **JWT-claim-based role check without minting the claim.** Policy references `auth.jwt() ->> 'role'`, but the auth flow never sets that claim — every check returns null, behavior is undefined.
- **RPC pattern: `SECURITY DEFINER` to "make it work."** Once added, the RPC bypasses RLS forever. Every parameter must be sanitized at function entry.
- **Joining org-scoped and global tables in a view, then querying the view from the client.** The view is RLS-on (since it inherits from base tables), but if the view filters on `auth.uid()` and one of the joins lacks RLS, you can leak.
- **n8n acting "as the system" to update a founder's row, no audit trail.** The founder's data changes without anyone knowing why.

# Anti-Patterns

- "We'll add RLS later, the app's the only client." n8n and any future direct DB connection are also clients.
- "Staff need to see everything, so we just use the service-role key in staff sessions." Now staff sessions are super-admin keys with no audit trail.
- Filtering by user in application code (`SELECT * WHERE user_id = ?`) and relying on the app to set that correctly. The user can bypass the app.
- "RLS is too slow." Almost always indexable; benchmark before disabling. Slow RLS is a performance ticket, not a security trade-off.

# Output Format

Each finding per `FINDINGS_SCHEMA.md`. Required deliverables for the audit:

1. **Executive summary** — one paragraph: is each of the four boundaries enforced at the data layer, or only at the UI layer? Specific gaps.
2. **Findings table** — boundary, table/folder/channel, severity, root cause, fix.
3. **The visibility matrix** — role × surface × table, with each cell `full | scoped | none | undefined`. Undefined cells are findings.
4. **Severity** per rubric.
5. **Evidence** — RLS policy snippet, query result demonstrating leakage, screenshot of Drive sharing dialog.
6. **Recommended fix** — almost always a specific RLS policy or a Drive-permission change. Cite the migration file and the policy SQL.
7. **Implementation complexity** — `small` to `medium`; `large` if the schema is missing the scoping column (`org_id`, `cohort_id`) and needs backfill.
8. **Owner/surface affected** — usually `supabase` + the user-facing surface; sometimes `drive`, `slack-bot`, or `n8n`.
9. **Follow-up questions** — product-level intent (e.g., "should mentors see each other's notes?").

# Example Prompt

> Audit QUAY's tenant, cohort, role, and service-account boundaries per `skills/quay/genius-team/multi-tenant-boundary-architect/SKILL.md`. For every Supabase table, declare RLS status and policy summary. Build the role × surface × table visibility matrix. Emit findings for every gap. Cite policy SQL and schema files. Do not change any policies or schema. Append to current audit board.

# Related Skills

- [auth-identity-architect](../auth-identity-architect/SKILL.md) — defines who the identities are; this skill enforces what they can see.
- [data-lifecycle-governor](../data-lifecycle-governor/SKILL.md) — where data lives across surfaces (Drive vs Supabase vs Sheets).
- [security-privacy-compliance-reviewer](../security-privacy-compliance-reviewer/SKILL.md) — broader privacy and least-privilege concerns.
- [adversarial-operations-reviewer](../adversarial-operations-reviewer/SKILL.md) — explicit "log in as a founder, try to read another's data" tests.
