---
name: quay-data-lifecycle-governor
description: Defines where every QUAY data object lives, who is the canonical source, what gets cached vs derived, what gets archived or deleted, and what audit trail exists. Catches data sprawl across Supabase / Drive / Sheets / Slack / n8n.
---

# Purpose

QUAY data lives in too many places: Supabase tables, Google Drive files, Google Sheets canonical stores, Slack messages, n8n execution logs, Read.ai outputs, and AI-generated artifacts. Without explicit rules, the same fact ends up in three places and starts to disagree. Worse, no one knows which copy is the truth.

This skill produces a **data ownership map**: for every meaningful object (member, mentor, cohort, proposal, intro, transcript, AI summary, activity event, etc.), it declares the canonical source, the allowed mirrors, the retention rule, the deletion rule, and the audit trail.

# When to Use

- During every `full` and `handoff` audit.
- When introducing a new data source (a new spreadsheet, a new API).
- When you notice the same fact in two places (e.g., founder names in Sheets and Supabase, drifting).
- Before any feature that promises "we'll delete your data if you ask."
- Before exposing data externally (to a client, to a mentor, to an API consumer).

# Expected Inputs

1. Supabase schema.
2. Drive folder map.
3. Sheets currently used as a system of record (mentor list, cohort roster, etc.).
4. n8n workflows that read or write any data store.
5. Slack channels treated as data (e.g., a "decisions" channel where staff log calls).
6. Read.ai output location.
7. AI artifact location (where do proposal drafts, transcript summaries, intelligence notes live?).

# Required Context to Inspect

- Supabase schema — every table.
- Drive folder hierarchy — at least the top two levels.
- All Google Sheets the project references in code or docs.
- n8n workflow exports — what they read, what they write.
- `skills/quay/activity-feed-model/SKILL.md` — the activity feed is one canonical source for events.
- `skills/quay/n8n-boundaries/SKILL.md` — declares "Supabase is the source of truth for entities."

# Review Methodology

For every domain object, produce an entry in the **data ownership table**. Anything missing is a finding.

## Data ownership table (one row per object)

| Object | Canonical source | Authorized writers | Authorized readers | Mirrors (allowed) | Mirrors (forbidden) | Retention | Deletion semantics | Audit trail |
|---|---|---|---|---|---|---|---|---|

Example rows (illustrative — verify in the actual repo):

| Founder profile | Supabase `members` | Staff via portal-internal; founder via portal-client (limited fields) | Staff (full), founder (self, limited), mentor (name + cohort) | n8n cache for Slack name resolution | Sheets duplicate | Active + 7 years post-cohort | Soft-delete with anonymization after 7 years; activity events retained | `activity_event` rows |
| Mentor list | Supabase `mentors` | Staff via mentor CRM | Staff, founders introduced to them | n8n cache | Standalone Sheet treated as truth | Indefinite | Soft-delete | `activity_event` rows |
| Cohort roster | Supabase `cohort_members` | Staff at cohort start | All cohort founders, staff, assigned mentors | Slack channel membership (derived) | Sheets | Indefinite | Tombstone | `activity_event` rows |
| Proposal | Supabase `proposals` | Founder (drafts), staff (decisions) | Founder (own), staff, reviewing mentor | Slack message (derived view) | Drive PDF (only if exported) | Active + 2 years | Hard-delete on founder request, tombstone otherwise | `activity_event` |
| Read.ai transcript (raw) | Drive folder per meeting | Read.ai integration | Staff | Supabase `transcripts.url` reference | Slack copy-paste | 1 year, then archive | Manual | n8n execution log |
| Transcript summary (AI) | Supabase `transcript_summaries` | AI pipeline (n8n) | Staff; founders if marked shareable | Slack post (derived) | Drive Doc | Active + 2 years | Hard-delete with parent | `activity_event` |
| Activity event | Supabase `activity_events` | Append-only by all surfaces via RPC | Staff (full), founder (self), mentor (assigned) | None | None — append-only | Indefinite | Never deleted; user-deletion produces tombstone events | Self |
| Slack messages | Slack workspace | Bot + humans | Channel members | None — Slack is the canonical surface | Don't store Slack message contents in Supabase | Slack default | Slack default | Slack audit |

## The five rules this skill enforces

1. **One canonical source per fact.** If a fact lives in two places, declare which is canonical and how the other is updated.
2. **Mirrors are derived, not authored.** A mirror is generated from the canonical source on a schedule or event; it is not edited directly. A mirror that humans edit is a second canonical source — pick one.
3. **Sensitive data classification.** Each object is labeled: `public | internal | confidential | restricted`. Restricted data has special handling (e.g., transcripts marked "private/NDA").
4. **Retention is explicit.** Every object has an answer to "how long do we keep this?" "Forever" is a valid answer but must be explicit.
5. **Deletion is explicit.** Every object has an answer to "what happens when this is deleted?" — cascade, tombstone, anonymize, retain in audit only.

# Severity System

- **P0** — A fact has two canonical sources that drift and one of them is shown to founders/clients (e.g., founder names diverge between Sheets and Supabase; portal shows Supabase but staff edit Sheets). Or: confidential data (private transcripts) is stored without retention/deletion rules and is reachable by non-staff.
- **P1** — A mirror is edited directly by humans, creating a silent second source. Retention rules absent. Audit trail absent for a mutable object. AI artifact stored without a deletion path tied to its parent.
- **P2** — Sensitivity classification missing on some objects. Mirrors not refreshed on lifecycle changes. Audit trail exists but is not consumed by any surface.
- **P3** — Naming inconsistent across stores. Mirrors not labeled as such in the schema.

# Checklist

- [ ] Data ownership table exists with one row per significant object.
- [ ] Each row has canonical source, writers, readers, mirrors, retention, deletion, audit trail.
- [ ] No fact has two canonical sources without an explicit policy resolving them.
- [ ] No "Sheet of truth" is silently the canonical source for an entity that the app treats as Supabase-canonical.
- [ ] Every confidential object (transcripts, proposals containing NDA content, mentor private notes) has a sensitivity tag.
- [ ] Retention rules cover: active period, archival, hard-delete date.
- [ ] Deletion semantics defined: cascade, tombstone, anonymize, retain-in-audit-only.
- [ ] Activity event coverage: every mutation of every significant object emits an event.
- [ ] AI-generated artifacts have a parent object and inherit deletion from the parent.
- [ ] Caches (n8n hot caches, Slack ID mappings) have a TTL or refresh trigger.

# QUAY-Specific Questions

- Is the **mentor list** currently a Google Sheet that staff edit, while the app reads a mirror in Supabase? If yes, that Sheet is the canonical source, and the app's "mentor CRM" is a glorified read-only view until someone decides to switch.
- The **activity feed**: is it append-only? Are there any mutation paths to existing events? Any path that updates an event is a violation.
- **Read.ai transcripts**: where do the raw transcripts live (Drive folder), where do the AI summaries live (Supabase), and how is the link between them stored? What happens if the Drive file is deleted?
- **AI artifacts** (proposal drafts, summaries, intelligence notes): are they versioned? Can a staff member see the prior draft? If not, "the AI just changed our document" is unrecoverable.
- **Slack as data**: do any decisions live exclusively in Slack threads? If yes, those decisions disappear when Slack history rolls. Sensitive ones should be mirrored to Supabase with attribution.
- **Founder-deletion**: if a founder asks for their data to be deleted (GDPR-style), what happens? Today: probably nothing automated. Plan: ?
- **Cohort archival**: at the end of a cohort, what changes? Anything? Should some data be moved out of the hot tables into an archive?

# Common Failure Modes

- **The Spreadsheet that won't die.** A Sheet is the canonical source for mentor info, but the app reads Supabase. Staff edit the Sheet; n8n syncs once a day; everyone treats the app's view as current. It isn't.
- **Two summaries of the same transcript.** The n8n workflow ran twice and wrote two rows. Now the dashboard shows the older one because of an ordering bug.
- **AI artifacts without parents.** An AI-generated summary sits in a table but its parent meeting/proposal was deleted. Orphaned forever.
- **Slack as the canonical decision log.** "We decided in #ops on the 14th" — the message is no longer searchable, and no one wrote it down anywhere durable.
- **No deletion path.** A founder leaves, asks for data deletion, and the team is left manually deleting rows across 7 tables, two Drive folders, and a Sheet. Some get missed.
- **Mirrors updated on a cron, not on change.** Founder name changes in Supabase; the Slack channel topic still shows the old name for 24 hours.

# Anti-Patterns

- "It's in the spreadsheet for now, we'll migrate later." Migrations don't happen. The spreadsheet is the system.
- Treating Slack messages as a database — searchable, sortable, persistent. None of those things are true.
- Caching AI summaries forever because "regenerating is expensive" — but never invalidating when the source meeting/proposal changes.
- Soft-delete columns (`deleted_at`) added but not consistently respected in queries.
- Append-only tables that aren't (a single UPDATE migration broke the contract a year ago).

# Output Format

1. **Executive summary** — one paragraph: does QUAY have a coherent data ownership model, and where does it leak?
2. **The data ownership table** — produced or updated based on inspection. This is the headline artifact for this skill.
3. **Findings table** — object, gap (canonical undefined / mirror authored / retention missing / etc.), severity, fix.
4. **Severity** per rubric.
5. **Evidence** — schema, sheet ID, Drive folder path, n8n workflow node.
6. **Recommended fix** — usually one of: (a) declare canonical source in a doc + migration if the schema lacks it, (b) make the mirror read-only, (c) add a retention policy + cron, (d) add an audit-trail column or activity event.
7. **Implementation complexity** — `small` for declaring rules; `medium` for adding audit/retention logic; `large` for backfilling state into legacy data.
8. **Owner/surface affected** — typically `supabase`, `drive`, `sheets`, and the surface that consumes the data.
9. **Follow-up questions** — product intent on retention windows, deletion semantics, GDPR posture.

# Example Prompt

> Build the QUAY data ownership table per `skills/quay/genius-team/data-lifecycle-governor/SKILL.md`. Inspect Supabase schema, Drive folder structure, the mentor/cohort Sheets, n8n workflows, and the activity feed. Identify every fact with multiple canonical sources, every mirror that is edited directly, every object without retention or deletion rules. Emit findings per `FINDINGS_SCHEMA.md`. Do not modify any data or schema. Append to current audit board.

# Related Skills

- [lifecycle-state-machine-auditor](../lifecycle-state-machine-auditor/SKILL.md) — states drive retention.
- [multi-tenant-boundary-architect](../multi-tenant-boundary-architect/SKILL.md) — who can see which data.
- [security-privacy-compliance-reviewer](../security-privacy-compliance-reviewer/SKILL.md) — sensitive data handling, NDA-marked content.
- [ai-governance-cost-optimizer](../ai-governance-cost-optimizer/SKILL.md) — AI artifacts as a distinct data class.
