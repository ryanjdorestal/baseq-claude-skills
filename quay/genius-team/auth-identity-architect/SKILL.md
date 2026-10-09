---
name: quay-auth-identity-architect
description: Audits QUAY's authentication, identity, role assignment, and session lifecycle. Distinguishes "auth that works in dev" from "auth a real client institution would accept."
---

# Purpose

Auth is QUAY's most under-built and most consequential surface. Staff log in with Google. Founders log in with magic link or invite. Mentors may or may not have logins at all. Clients (institutions paying for cohorts) don't exist yet but will. A dev-bypass role switcher probably exists somewhere. None of this has been hardened.

This skill produces a complete identity model for QUAY — who can be who, how they become that, how they stop being that, what they can do while they are that — and finds the gaps where today's implementation breaks the model.

# When to Use

- Before exposing the platform to any external client institution.
- Before onboarding a non-Ryan staff member to administer the platform.
- When adding any new role, surface, or login flow.
- When adding founder-facing features that previously were staff-only (or vice versa).
- During every `pre-deploy` and `handoff` audit.

# Expected Inputs

1. The auth code: middleware, login routes, session handlers, role checks.
2. Supabase auth configuration (providers enabled, redirect URLs, JWT claims).
3. Slack bot identity mapping (Slack user → QUAY identity).
4. The dev-bypass mechanism if one exists (role switcher, mock user, header impersonation).
5. The current role definitions (staff, founder, mentor, client-admin, etc.) and where they're declared.
6. Any "internal tools" routes that aren't protected the same way as user routes.

# Required Context to Inspect

- `middleware.ts` / `middleware.js` (Next.js auth middleware)
- Supabase auth provider config (in dashboard or `supabase/config.toml`)
- `lib/auth/*`, `lib/session/*`, `lib/rbac/*`, or equivalents
- Slack bot's identity-mapping code (typically `slack-bot/identity.ts` or similar)
- Any `.env.example` for auth-related variables — flag any missing-in-example
- Login UI(s): `/login`, `/invite`, `/auth/callback`, magic-link handler
- `skills/quay/supabase-schema/SKILL.md` for the declared RLS contract
- Drive service account JSON location (file system, not contents)

# Review Methodology

The audit walks four lifecycles end-to-end and one cross-cutting concern.

## 1. Login lifecycle (per role)

For each role (staff, founder, mentor, client-admin):
- How does this role acquire a session? (Google SSO, magic link, invite token, impersonation by staff?)
- Where is the session stored, with what expiry?
- What happens on refresh? On logout? On password change (for SSO-backed accounts, on Google account revocation)?
- What JWT claims does Supabase issue? Are they used by RLS, by the app, by both?
- Can a non-role user reach this login flow? (e.g., can a founder hit the staff Google SSO callback and get a session?)

## 2. Role assignment lifecycle

- Who can assign a role? (Staff-only? Auto-derived from email domain? From an invite token?)
- Where is the role written? (`auth.users.user_metadata`? a `public.profiles.role` column? Both — and which wins?)
- What happens if a user has conflicting roles in two places?
- Can a user **change their own role** via any path — API, settings page, JWT claim manipulation?

## 3. Account lifecycle (cradle to grave)

- Invite issued → accepted → active → paused → revoked → deleted. Which states exist? Which transitions are implemented?
- Is there a "disabled" state distinct from "deleted"? (There should be.)
- What happens when a founder finishes the cohort? Does their account persist? In what state?
- What happens to a mentor who stops participating? Are their old intros still attached?
- What happens to data owned by a deleted user? (Cascade? Soft-delete? Orphan?)

## 4. Session/dev-bypass cross-cut

- Is there a "switch role" / "view as" / "impersonate" feature? Is it gated to staff?
- Is there a dev-only bypass (header, env flag, role switcher in UI)?
- **Can the dev bypass ship to production?** This is the most common P0.
- Are session cookies `HttpOnly`, `Secure`, `SameSite=Lax/Strict`?
- Are JWTs short-lived with refresh tokens, or long-lived bearer tokens?
- Is there any service-account or service-role key reachable from the *client* bundle? (Should be never.)

## 5. The integration-identity question

- Slack: how is a Slack user ID mapped to a QUAY identity? What if the mapping is missing or wrong?
- n8n: which credentials does n8n hold, and which roles' actions do they perform? Is n8n always acting as "the system" or sometimes "as a user"?
- Drive: does QUAY use a service account, an OAuth user, or both? Whose Drive does it touch?
- Read.ai: how does QUAY verify a transcript came from a meeting that involved a real QUAY member?

# Severity System

- **P0** — Any of:
  - Dev-bypass mechanism reachable in production (role switcher, mock JWT, debug header).
  - Founders can authenticate as staff or impersonate other founders.
  - Service-role key or service-account JSON reachable from a client bundle / public URL / unprotected route.
  - Login route that grants a session without verifying the user owns the identity (e.g., magic link doesn't expire or is bound to nothing).
  - JWT claims used for authorization can be set by the user (e.g., role stored in `user_metadata` which the user can edit).
- **P1** — Role assignment exists but is not enforced consistently (RLS uses `auth.uid()` but middleware uses a different role source). No revocation/disabled state. Session expiry not set. Magic-link tokens reusable. Slack identity mapping has no verification path.
- **P2** — Role conflicts can occur (role in two places, no resolution rule). Long-lived sessions. No audit log of role changes. No "view as" for staff to debug what a founder sees.
- **P3** — Login UI doesn't tell users which role they're currently in. No "switch account" affordance.

# Checklist

- [ ] One authoritative role source per identity. (Not split across `user_metadata` and a `profiles` table without a defined precedence.)
- [ ] Role source is not writable by the user it describes.
- [ ] Every login flow has a defined session expiry.
- [ ] Magic link tokens are single-use and time-limited (≤ 15 min recommended; ≤ 1 hour absolute max).
- [ ] Google SSO is scoped to a specific Workspace domain for staff; founders cannot complete the staff flow.
- [ ] No service-role key in the client bundle. Verify with `grep -r SERVICE_ROLE` against the built artifact, not just the source.
- [ ] Dev-bypass mechanism is gated by an env var that is **definitionally false** in production and is **proven** by a test or build-time assertion.
- [ ] Account lifecycle states are modeled: `invited → active → paused → revoked → deleted`. Each transition has a who/when/why.
- [ ] Deleted accounts have a defined data-handling policy (cascade vs orphan-with-tombstone).
- [ ] All "internal tools" routes are protected by the same middleware as user routes.
- [ ] Slack user → QUAY identity mapping has a verification path; unmapped users are explicitly denied, not implicitly granted.
- [ ] An audit log records role changes, login events, and impersonations. (May hand off to `observability-telemetry-architect` to confirm the log is consumed.)

# QUAY-Specific Questions

- Are staff logging in via Google Workspace (`@quay-domain`), or via personal Google accounts? Workspace is required for institutional-grade.
- Is there a "demo founder" account used for screenshots / stakeholder demos? Where does it live? Is it disabled in prod?
- The Base44 clone may have its own auth assumptions baked in. Do they conflict with the QUAY model?
- When a mentor is added to the CRM, do they get a login automatically, never, or on demand? What's the intended answer?
- Is the activity feed reachable by founders? If so, is it filtered by RLS, or by app code? (RLS is required.)
- Does `n8n` ever post to Supabase as a specific user (via JWT) or always as the system (via service-role)? When it acts "as a user," whose JWT does it use?

# Common Failure Modes

- **The "dev role switcher in production" pattern.** A UI dropdown to pick staff/founder/mentor that was meant for development gets shipped. Anyone visiting can become anyone.
- **Magic links that don't expire** or are reusable. Sent to email; email leaks; account compromised forever.
- **Role stored in `user_metadata`.** Supabase allows the user to update their own user_metadata via the auth API. Setting `role: "staff"` in user_metadata and trusting it for authz is a known critical pattern.
- **Service-role key in `NEXT_PUBLIC_*` env var.** Anything `NEXT_PUBLIC_*` ships to the browser.
- **Middleware that whitelists `/internal/*` paths assuming they're "private" without actually checking auth.**
- **Slack handler that trusts the `user.email` from Slack as the QUAY identity** without verifying that the email maps to an existing QUAY user — anyone in the Slack workspace becomes a QUAY user.
- **"Just log in as staff for now" hardcoded somewhere** to make dev easier, then forgotten.

# Anti-Patterns

- Authorization checks in the UI ("if (user.role === 'staff') showButton") with no corresponding RLS or server-side check.
- "Don't show that route in nav" treated as access control.
- One auth provider for everyone with role inferred from email domain, with no override path for exceptions.
- Long-lived API tokens for "the founder portal" that bypass RLS.
- Reusing the same Supabase project for staging and prod (different schemas don't count — separate projects are required for credentials hygiene).

# Output Format

Each auth finding per `FINDINGS_SCHEMA.md`. Required:

1. **Executive summary** — one paragraph: does QUAY have an institutional-grade auth posture? Specific gaps in P0 order.
2. **Findings table** — finding ID, role/flow affected, severity, root cause, suggested fix.
3. **Severity** — strictly per the rubric.
4. **Evidence** — `middleware.ts:42`, `lib/auth/role.ts:91`, JWT claim sample, Supabase auth config screenshot description.
5. **Recommended fix** — specific code change, RLS policy, config change, or process change. Cite the file.
6. **Implementation complexity** — most P0 auth fixes are `small` to `medium`. If a fix is `large`, the finding may be hiding two.
7. **Owner/surface affected** — `auth`, `supabase`, `portal-internal`, `portal-client`, `slack-bot`.
8. **Follow-up questions** — typically about product intent ("Should mentors ever log in?").
9. **"Do not fix yet"** — rare in auth. If invoked, must justify why the gap is acceptable for one more sprint.

# Example Prompt

> Audit QUAY's auth surface per `skills/quay/genius-team/auth-identity-architect/SKILL.md`. Inspect middleware, Supabase auth config, login routes, magic link handlers, Slack identity mapping, and any dev-bypass mechanism. Identify all account lifecycle states currently implemented vs declared. Emit findings per `FINDINGS_SCHEMA.md`. Do not modify any auth code. Cite file:line for every finding. Maximum 5 P0s — if you find more than 5, sort by blast-radius and write the rest as P1.

# Related Skills

- [multi-tenant-boundary-architect](../multi-tenant-boundary-architect/SKILL.md) — once identity is settled, this skill ensures each identity sees only its tenant's data.
- [security-privacy-compliance-reviewer](../security-privacy-compliance-reviewer/SKILL.md) — service-account permissions, secret storage, audit logs.
- [lifecycle-state-machine-auditor](../lifecycle-state-machine-auditor/SKILL.md) — formalizes the account lifecycle this skill outlines.
- [adversarial-operations-reviewer](../adversarial-operations-reviewer/SKILL.md) — tests "what would an attacker / curious founder try."
