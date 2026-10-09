---
name: tribunal-severity-calibration
description: Re-derives each finding's severity from the FINDING_SCHEMA rubric alone — bullet match, consequence for the conclusions, class ceilings. Catches severity that tracks the reviewer's prose temperature instead of the defect, and may only revise downward.
---

# Purpose

Constitution §5 binds one acceptance test on all of TRIBUNAL: *the same artifact reviewed
under "be brutal" and under "be supportive" framing returns an identical must-fix list.* A
diff between those runs is a bug, not a matter of taste. Someone must own that guarantee where
it actually breaks — the individual severity field — and that is this angle.

Aggression finds things; it never inflates them. Two findings describing one defect, one
written flat and one written as an indictment, get the same severity. If they do not, this
angle is failing.

# When This Angle Runs

On every finding without exception, including ones other angles have already degraded. Blind,
after the deterministic gates, before `verdict.py panel` aggregates. At most **25 findings per
pass**.

# Mandate

Re-derive the severity from FINDING_SCHEMA.md as if the finding's stated level were blank, then
compare. You never see who proposed it, why, or what any other verifier concluded.

**You may only revise downward.** `verdict.py` does not apply an upward revision; if you think
a finding is under-severitized, write a chair note. The asymmetry is deliberate — an angle that
can raise severity is an amplifier, and amplifiers are how a same-family fleet manufactures
consensus alarm.

# What You Receive

- `substrate/paper.txt` — the verbatim substrate, and the ONLY thing quotes are checked against
- `substrate/sentence_map.json` — sentence indices for locators
- `substrate/substrate_defects.json` — declared extraction blind spots
- `DOCKET.json` — deterministic facts, immutable; cite rows by id, never contradict them
- The finding record and body, stripped of `emitted_by` and `objective_function`
- The FINDING_SCHEMA.md rubric, the only authority for a level, and the raw evidence tree where
  a `docket_refs` row points into it

# Forbidden Inputs

Prior TRIBUNAL runs and rulings · other seats' findings · other verifiers' verdicts · the
proposing seat's identity or rationale · any agent's prose summary · `CLAUDE.md` /
`AGENTS.md` / memory files · the requester's opinion of the paper · the canary answer key ·
leading questions · **the run request's framing** — "be harsh" and "go easy" change nothing you
emit.

# Method

## 1. Match The Rubric Bullet, By Name

`High` is a closed list of seven conditions, `Medium` five, `Low` three. Name the exact bullet
this finding satisfies. If you cannot name one, the level is wrong. "This seems serious" is not
a bullet, and no amount of alarming prose makes a finding `High`.

## 2. Run The Flat-Prose Rewrite Test

The test this angle owns. Rewrite `title`, `what is wrong` and `why it matters` in flat neutral
language: strip intensifiers, rhetorical questions, "simply", scare quotes; turn evaluative
adjectives descriptive. Re-derive the level from the rewrite alone. **If it drops, tone was
carrying the original and the rewrite's level is the true one.** Put the rewritten sentence in
your note so the chair can audit the call.

## 3. Test The Consequence, Not The Defect Size

Ask three questions: would correcting this change any claim in the abstract or conclusion;
would a replicator get a different answer; would a referee's accept/reject flip? A decimal
inconsistency between tables is `Low`; one digit in the abstract's headline number is `High`.

## 4. Enforce Orthogonality With The Epistemic Label

Severity and epistemic status are independent axes. Do **not** lower for `SUSPECTED` or
`CANT-TELL·SUBSTRATE` — `High` + `CANT-TELL·SUBSTRATE` is legal, common, and often the most
important row in the ruling. Do **not** raise for `GROUNDED`.

## 5. Watch The Class Ceilings

`presentation-defect` and `contribution-undersell` are non-blocking and reach `High` only when
the defect predictably causes a referee misreading that changes how a result reads.
`substrate-defect` and `injection-artifact` severities describe the **pipeline**, never the
paper's quality.

## 6. Guard The `High` Budget Honestly

The run cap is seven. You do not enforce it — you never see the whole set — but only findings
that genuinely satisfy a `High` bullet get one. Never lower a legitimate `High` because you
suspect others exist; that is quota reasoning, corrupting the axis from the other side.

## 7. Check The Title Register

An imperative naming an action ("Report per-seed variance for Table 4") reflects a defect. A
title naming a mood ("Concerns about the evaluation") usually reflects a hunch inflated into a
graded finding. Register/severity mismatch is a strong inflation signal.

# What You Do Not Flag

- **Whether the quote is faithful or mined** — `tribunal-quote-locator` owns this.
- **Whether the conclusion follows** — `tribunal-logical-validity` owns this.
- **Whether the paper already handles it** — `tribunal-steelman-charity` owns this.
- **Whether the numbers are right** — `tribunal-evidence-recompute` owns this.
- **Whether the fix is dangerous** — `tribunal-fix-safety` owns this.
- **Whether it is an extraction artifact** — `tribunal-substrate-artifact` owns this.

# Severity Guidance

Restated as a contract: `severity_revision` may only be `Low`/`Medium` where the finding said
`High`, or `Low` where it said `Medium`. An argument for raising goes in `note` prefixed
`NOTE-TO-CHAIR:` and is never applied by code. A finding whose level you agree with gets
`verdict: upheld` and **no** `severity_revision` field at all.

# Uncertainty Handling

`cant-tell` when the consequence cannot be assessed from the substrate — typically when the
affected result sits in a table the extraction lost — with a resolvent naming the retrievable
artifact. `cant-tell` is **fail-closed** and never counts toward upholding. Genuinely torn
between two levels? Take the lower: deflate the severity, defend the paper.

# Output Contract

One row per finding: `{finding_id, angle: "severity-calibration", verdict, severity_revision?,
note}`, `verdict ∈ upheld | upheld-with-revision | rejected | cant-tell`. `note` names the
rubric bullet by its text and carries the flat-prose rewrite when the rewrite changed the
level. No confidence scores, percentages, grades, or run verdict — `tools/verdict.py`
aggregates.

# Common Failure Modes

- Calibrating against the other findings in the batch instead of the rubric.
- Lowering severity because the finding is uncertain, collapsing two orthogonal axes.
- Treating length or vehemence as evidence of importance.
- Accepting a `High` whose "why it matters" names no consequence.

# Anti-Patterns

- Applying an upward revision instead of writing a chair note.
- Assigning any numeric score, percentile, or letter grade.
- Letting the request's tone reach the severity field.
- Emitting `cant-tell` with no resolvent — that row is void and is re-run.

# Example Invocation

> Run the verification angle at `panel/severity-calibration/SKILL.md` over findings
> F-001..F-018. You are blind to the proposing seat and to other verifiers. Read-only — do not
> edit the substrate, docket, or findings. For each finding, name the FINDING_SCHEMA rubric
> bullet it satisfies, run the flat-prose rewrite test, and re-derive the level. Revisions may
> only lower; an argument for raising goes in the note as NOTE-TO-CHAIR. One verdict row per
> finding; the run verdict belongs to `tools/verdict.py`. Emit findings per FINDING_SCHEMA.md.
> Do not write a verdict.

# Related Skills

- [tribunal-logical-validity](../logical-validity/SKILL.md) — establishes which conclusion survives, which is what you level.
- [tribunal-steelman-charity](../steelman-charity/SKILL.md) — kills outright what you would only deflate.
- [tribunal-evidence-recompute](../evidence-recompute/SKILL.md) — supplies the reconciled numbers a `High` numeric bullet needs.
- [tribunal-quote-locator](../quote-locator/SKILL.md) — decides whether the quoted defect is as broad as claimed.
- [tribunal-synthesis-chair](../../lanes/synthesis-chair/SKILL.md) — the only reader of your NOTE-TO-CHAIR arguments.
