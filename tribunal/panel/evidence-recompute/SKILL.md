---
name: tribunal-evidence-recompute
description: Independently re-derives the numbers a finding rests on from the raw evidence tree and DOCKET rows before reading the finding's own arithmetic — deltas, percentages, aggregation level, row support. Catches findings citing a real docket row for a conclusion it does not support.
---

# Purpose

A finding can cite a genuine `verified` docket row and still be wrong about what it means.
DOCKET_SCHEMA.md is explicit: a `verified` row certifies that the cited evidence exists and the
number matches, and says **nothing** about whether the number supports the claim attached to it.
That is stage 2, and this angle is where stage 2 happens.

The method is the point. You re-derive first and read the finding's arithmetic second, because
reading it first anchors you: once you have seen "12.8%", every recomputation converges on
12.8% and the check becomes theatre. Independence here is procedural, not a matter of resolve.

# When This Angle Runs

On every finding whose argument contains a number, delta, percentage, aggregation, or
`docket_refs` entry — in practice every `numeric-mismatch`, `statistical-inconsistency`,
`figure-table-mismatch` and `data-integrity` finding. Blind, after the deterministic gates,
before `verdict.py panel` aggregates. At most **25 findings per pass**.

# Mandate

Reproduce the arithmetic from primary sources, then compare. Two obligations beyond the sums:

1. **Confirm the docket row supports the use the finding makes of it.** A row saying
   `results/main_eval.json $.eval.accuracy = 85.28` supports "the paper's 85.3 is that file's
   number". It does not support "the method beats the baseline" or "this is the strongest
   baseline".
2. **Never guess.** If the raw file is not present, the verdict is `cant-tell` with a resolvent.
   A recomputation from a remembered or assumed value is fabrication (Constitution §2).

# What You Receive

- The raw evidence tree — `results/`, configs, code, logs — read directly
- `DOCKET.json` — immutable; cite rows by id. `evidence-manifest` rows say which paths are
  `present` / `missing` / `unreadable`.
- `substrate/paper.txt` — the verbatim substrate, and the ONLY thing quotes are checked against
- `substrate/sentence_map.json` — sentence indices for locators
- `substrate/substrate_defects.json` — declared extraction blind spots
- The finding record, stripped of `emitted_by` and `objective_function`

# Forbidden Inputs

Prior TRIBUNAL runs and rulings · other seats' findings · other verifiers' verdicts · the
proposing seat's identity or rationale · any agent's prose summary · `CLAUDE.md` / `AGENTS.md` /
memory files · the requester's opinion of the paper · the canary answer key · leading questions ·
**the finding's own Evidence section and arithmetic, until step 3**.

# Method

## 1. Extract The Question Without The Answer

From `title` and `locator`, state what needs computing in one line — "relative improvement of
ours over the strongest baseline in Table 4". Do not read the finding's `Evidence` yet. Write
the question down before opening a file.

## 2. Recompute From Primary Sources

Open the raw files named by the relevant `docket_refs` and by the paper's pointers, pull the
values yourself, and compute — stating formula and inputs. Apply the docket's discipline:
numeric-token equality (`73.2` matches `73.20`; `73` does not match `73.5`), and only standard
rounding to displayed precision is legal (84.7 → 85 fine; 84.7 → 85.3 is a mismatch).

## 3. Now Read The Finding's Arithmetic And Diff It

They agree → `upheld` on this axis. They disagree and yours is defensible → `rejected`, both
computations in your note. They disagree because the finding used a different but legitimate
definition → `upheld-with-revision`, naming the ambiguity; relative gain vs. absolute points is
the standard offender.

## 4. Test Each `docket_refs` Row For Actual Support

A `stat-consistency` row with `status: insufficient_data` is a **missing-reporting** fact, never
an inconsistency. A `citation` row with `context: unchecked` cannot support a `citation-misuse`
claim. A `numeric-claim` with `match_class: rounded` is not a discrepancy. `ambiguous_mapping`
supports nothing. An `evidence-manifest` `present` says the file exists, not what it contains —
open it.

## 5. Check The Aggregation Level

The most frequent real error in this class: a number computed over the wrong population. Is the
value the mean of seeds, the best seed, a single run, a micro- or macro-average — and is the
paper's number the same thing? Read key names, array lengths and seed fields rather than
assuming. A max compared against a mean is a defect wherever it occurs, including inside a
finding.

## 6. Reconcile Percentages Against N

Recompute reported percentages from counts where counts exist. A percentage no integer count
over the stated N can produce is inconsistent; one whose implied N differs from the stated N
means the denominator changed silently.

## 7. Stop At The Boundary Of The Evidence

If the file is absent or unreadable, stop. Do not substitute a plausible value, infer from an
adjacent run, or use the paper's own number as a proxy for the raw one — that makes the check
circular.

# What You Do Not Flag

- **Whether the quote is faithful** — `tribunal-quote-locator` owns this.
- **Whether the inference from a correct number is valid** — `tribunal-logical-validity` owns this.
- **Whether the severity is right** — `tribunal-severity-calibration` owns this.
- **Whether the paper explains the discrepancy** — `tribunal-steelman-charity` owns this.
- **Whether the fix is safe** — `tribunal-fix-safety` owns this.
- **Whether a lost table caused the confusion** — `tribunal-substrate-artifact` owns this.

# Severity Guidance

`severity_revision` may only **lower** — lower when the discrepancy is real but smaller than
claimed, a rounding-boundary case rather than a misreported result. A discrepancy you confirm in
the direction that supports the paper satisfies a `High` bullet; you do not raise it yourself,
you write `NOTE-TO-CHAIR:` and let the chair see the argument.

# Uncertainty Handling

`cant-tell` whenever the raw file is absent, unreadable, unparseable, or ambiguous about which
field the paper used. Never a guess. The resolvent names the artifact and what is needed:
`results/ablation_seed*.json — need per-seed accuracy for Table 4 row 3; the paper reports one
number and does not say whether it is mean or best.` Vague resolvents void the row. Fail-closed:
never counts toward upholding. Two defensible computations the evidence cannot separate is
`cant-tell`, not a coin flip.

# Output Contract

One row per finding: `{finding_id, angle: "evidence-recompute", verdict, severity_revision?,
recomputation, note}`, `verdict ∈ upheld | upheld-with-revision | rejected | cant-tell`.
`recomputation` states formula, inputs, source paths and result; `note` records by id any
`docket_refs` row that does not support the use made of it. No confidence scores, no run verdict.

# Common Failure Modes

- Reading the finding's arithmetic first and then "verifying" it.
- Treating a `verified` row as endorsement of the claim attached to it.
- Recomputing from the paper's table instead of the raw file, which checks nothing.
- Comparing a rounded display value to a raw value and calling it a mismatch.

# Anti-Patterns

- Any number in your output you did not read from a file or compute in front of the reader.
- Editing or contradicting `DOCKET.json`; disagreement is a `substrate-defect` finding.
- Emitting `cant-tell` with no resolvent — that row is void and is re-run.
- Reporting a confidence, tolerance band, or probability that the number is right.

# Example Invocation

> Run the verification angle at `panel/evidence-recompute/SKILL.md` over findings F-001..F-018.
> You are blind to the proposing seat and to other verifiers. Read-only — do not edit the
> evidence tree, docket, substrate, or findings. For each finding, state the quantity to be
> computed from the title and locator alone, recompute it from the raw files and `docket_refs`
> rows **before** reading the finding's own arithmetic, then diff. Where the raw file is absent,
> emit `cant-tell` with a resolvent — never a guess. One verdict row per finding; the run verdict
> belongs to `tools/verdict.py`. Emit findings per FINDING_SCHEMA.md. Do not write a verdict.

# Related Skills

- [tribunal-substrate-artifact](../substrate-artifact/SKILL.md) — decides whether an irreconcilable number was mangled by extraction.
- [tribunal-logical-validity](../logical-validity/SKILL.md) — tests the conclusion drawn from your confirmed numbers.
- [tribunal-fix-safety](../fix-safety/SKILL.md) — needs your read on whether the number a fix requires exists.
- [tribunal-severity-calibration](../severity-calibration/SKILL.md) — levels the finding once the true magnitude is known.
- [tribunal-substrate-escalation](../../lanes/substrate-escalation/SKILL.md) — re-acquires the raw files behind your `cant-tell`s.
