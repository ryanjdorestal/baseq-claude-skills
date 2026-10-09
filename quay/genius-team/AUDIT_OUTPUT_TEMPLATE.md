# Audit Board Template

Every Genius-Team audit produces **one** board following this template. The board lives at:

```
skills/quay/genius-team/audits/<YYYY-MM-DD>-<mode>/AUDIT.md
```

with sibling files:

```
audits/<YYYY-MM-DD>-<mode>/
  AUDIT.md             ← this template
  findings/
    <finding_id>.md    ← one per finding, shaped per FINDINGS_SCHEMA.md
  tasks/
    <task_id>.md       ← one per accepted task, shaped per IMPLEMENTATION_TASK_SCHEMA.md
```

The board is the **only** artifact that needs to be read end-to-end. Findings and tasks are detail files you open from the board.

---

## Template

```markdown
# QUAY Platform Audit — <mode>

**Date:** <YYYY-MM-DD>
**Audit mode:** <full | quick | pre-deploy | handoff | n8n-only | auth-security | ai-cost>
**Run by:** <human name or "Claude Code session">
**Scope:** <one sentence — what surfaces / branches / time window>
**Branch / commit:** <ref>

---

## 1. Scope

- Surfaces inspected: <slack-bot, portal-internal, portal-client, n8n, supabase, drive, readai, sheets, ai, docs>
- Time window: <last sprint | since YYYY-MM-DD | initial baseline>
- Skills run, in order: <list>

## 2. Files / workflows inspected

Concrete list with line counts where useful. Examples:

- `slack-bot/handlers/proposals.ts` (412 lines)
- `n8n/workflows/readai-ingest.json` (nodes: 14)
- `supabase/migrations/2026*.sql` (8 migrations)
- `docs/QUAY_OS.md`, `docs/SYSTEM_MAP.md`
- Drive folders inspected: `Quay / Cohorts / *`, `Quay / Mentors / *`

If a surface was **not** inspected, say so explicitly: "Drive folder permissions: NOT INSPECTED — no API access in this session."

## 3. Assumptions

What this audit took as given. Future auditors should challenge these if circumstances change.

- "There is exactly one production Slack workspace."
- "n8n Cloud is the only n8n environment."
- "Supabase project ref is X; service-role key is held only by n8n credentials and a single staff vault entry."
- "No external clients have founder access yet — clients view via internal staff."

## 4. Severity summary

| Severity | Count | Trend vs prior audit |
|---|---|---|
| P0 (blocker) | <n> | <+/- vs prior> |
| P1 (serious) | <n> | <+/- vs prior> |
| P2 (important) | <n> | <+/- vs prior> |
| P3 (polish) | <n> | <+/- vs prior> |

If this is the first audit, write "baseline" under trend.

## 5. P0 findings — must fix before next deploy or handoff

| ID | Title | Surface | Owner | Status |
|---|---|---|---|---|
| F-001 | <one line> | <surface> | <name or "unassigned"> | accepted / deferred / waived |

Each row links to `findings/F-001.md`.

> **Rule:** Max 5 P0 findings per audit. If you have more, the severity rubric is being misapplied or the platform is on fire — in either case, stop and triage.

## 6. P1 findings — fix this sprint

| ID | Title | Surface | Recommended fix (one line) | Task |
|---|---|---|---|---|
| F-010 | <one line> | <surface> | <one line> | T-002 |

## 7. P2 findings — fix this quarter

Same shape, condensed.

## 8. P3 findings — polish / nice-to-have

Bulleted list only. No table. Examples:
- F-040: Internal dashboard typography drifts on long org names. → `findings/F-040.md`

## 9. Implementation task list

| Task ID | Title | Source findings | Priority | Estimate | Owner |
|---|---|---|---|---|---|
| T-001 | <imperative title> | F-001, F-003 | P0 | 4h | <name> |
| T-002 | <imperative title> | F-010 | P1 | 2h | unassigned |

Each row links to `tasks/T-001.md`.

> **Rule:** Every accepted P0 and P1 finding must produce at least one task. If a P0 has no task, the audit is incomplete.

## 10. Kill list — features/code to delete

Things the prioritizer or PM reviewer recommend cutting. Each entry: what, why, what's lost.

- `<feature>` — <one-line why> — Lost: <what use-case disappears>

## 11. Defer list — explicitly not doing this audit cycle

Findings the team agreed not to fix yet. Each must have a `defer_until` date.

| ID | Title | Defer until | Reason |
|---|---|---|---|
| F-022 | <one line> | YYYY-MM-DD | <one line> |

## 12. Waiver list — accepted-as-is

Things the team explicitly accepts as risk, with expiration. Waivers expire automatically — an expired waiver becomes a P1 in the next audit.

| ID | Title | Waived until | Reason | Approver |
|---|---|---|---|---|

## 13. Risk register — what could go wrong even if every task ships

A short list of structural risks the audit identified but cannot fully resolve through tasks. Examples:
- "n8n Cloud is a SPOF. No fallback orchestrator. Migrating off is multi-week."
- "Single staff member holds Slack app ownership."
- "No incident on-call rotation defined."

## 14. Unresolved questions

Open questions that block correct prioritization. Each question must have an owner and a date by which it needs an answer.

- Q1: Should mentor-CRM data be visible to founders, ever? Owner: Ryan. By: 2026-06-05.
- Q2: Is there a planned client (paying) before September? Owner: Ryan. By: 2026-06-01.

## 15. Skill-gap meta-findings

If a skill missed something a later skill caught, log it here so the SKILL.md can be updated.

- `n8n-workflow-reliability-engineer` did not flag absent idempotency on the readai-ingest workflow; caught by `integration-contract-reviewer`. → Update its checklist.

## 16. Recommended next sprint

A single short paragraph: given everything above, what should the team actually do next? Two to four sentences. No bullets, no fluff. This is the single piece of prose in the audit — make it count.

## 17. Sign-off

- Audit produced by: <Claude Code session id or human>
- Accepted by: <human name, date>
- Distribution: <where it was shared — link to Notion/Linear/etc. if applicable>
```

---

## Notes on using the template

- **Fill every section.** If a section has no content, write "none" — do not delete the section. Future auditors track diffs across boards.
- **No section may be "TBD."** If you don't know, write the unresolved question into §14.
- **The board is timestamped and immutable after sign-off.** New audit → new board. Do not edit a signed-off board to add findings after the fact.
- **Prefer short rows in tables.** If a finding needs explanation, that's what its individual `findings/<id>.md` file is for.
- **The board is for humans.** Tasks (`tasks/<id>.md`) are for future Claude Code sessions. Keep the audiences distinct.
