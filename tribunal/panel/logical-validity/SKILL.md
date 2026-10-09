---
name: tribunal-logical-validity
description: Tests whether a finding's conclusion follows from the evidence cited inside that finding — premise chains, non-sequiturs, equivocation, circularity, stated failure modes. Catches criticisms that are correctly quoted and still do not add up.
---

# Purpose

A finding can be perfectly grounded and still be wrong. The quote is real, the locator right,
the docket row exists — and the conclusion drawn from them does not follow. That is the most
common way a competent-looking review produces noise: a true premise, a true observation, and
an inferential jump nobody checked.

This angle checks the jump, taking the finding's evidence as given. Not "is the paper wrong" —
that is not your question and a finding record is not enough to answer it.

# When This Angle Runs

On every finding, with special force on `INFERRED` findings whose `inference_chain[]` names
the grounded premises. Blind, after the deterministic gates, before `verdict.py panel`
aggregates. At most **25 findings per pass**.

# Mandate

Attack the reasoning inside the finding. You never see who proposed it, why, or what any other
verifier concluded; you judge one finding at a time on its own merits.

Reason **only from what the finding cites**. If its argument needs a fact it did not supply,
the conclusion does not follow — supplying that fact yourself does the proposer's work and
launders your assumption into the record.

# What You Receive

- `substrate/paper.txt` — the verbatim substrate, and the ONLY thing quotes are checked against
- `substrate/sentence_map.json` — sentence indices for locators
- `substrate/substrate_defects.json` — declared extraction blind spots
- `DOCKET.json` — deterministic facts, immutable; cite rows by id, never contradict them
- The finding record with `quote`, `locator`, `docket_refs`, `inference_chain`,
  `why_unanchored` and body, stripped of `emitted_by` and `objective_function`
- The raw evidence tree only where a cited `docket_refs` row points into it

# Forbidden Inputs

Prior TRIBUNAL runs and rulings · other seats' findings · other verifiers' verdicts · the
proposing seat's identity or rationale · any agent's prose summary · `CLAUDE.md` /
`AGENTS.md` / memory files · the requester's opinion of the paper · the canary answer key ·
leading questions.

# Method

## 1. Reconstruct The Argument As Numbered Premises

Write it as P1, P2, … ⊢ C. Each premise must be the quote, a docket row by id, a finding named
in `inference_chain[]`, or a stated general principle. Any premise you supplied yourself is a
**suppressed premise** — name it and ask whether it is defensible. Most bad findings die here.

## 2. Walk The `inference_chain` Link By Link

Verify each id resolves to a `GROUNDED` finding or a docket row that says what the chain claims
it says. A link resting on a `SUSPECTED` finding makes the conclusion `SUSPECTED` at best and
the label wrong. A link resting on a rejected or nonexistent id is fatal.

## 3. Hunt Equivocation

One word, two senses. In this domain: "significant" (statistical vs. practical), "baseline"
(strongest vs. any reported), "improvement" (absolute points vs. relative gain), "held out"
(unseen at training vs. at tuning). Point at both occurrences and name both senses.

## 4. Test For Circularity

Does the finding assume what it sets out to show — arguing a claim is unsupported by
presupposing its evidence does not count? Also check whether "what would change my mind"
merely restates the conclusion.

## 5. Check The Stated Failure Mode Follows From The Stated Defect

A caption mismatch does not make a result unreproducible; a missing seed count does not make
the mean wrong. Real defect plus overreaching failure mode is `upheld-with-revision` and a
downward `severity_revision`, not a rejection.

## 6. Quantifier And Direction Discipline

Watch for "on this dataset" → "in general", "some" → "all", "correlated" → "causes", and above
all "not reported" → "not done". And when a finding alleges a number is overstated, check that
its argument establishes the **direction**, not merely a disagreement.

# What You Do Not Flag

- **Whether the quote is faithful to context** — `tribunal-quote-locator` owns this.
- **Whether the severity matches the rubric** — `tribunal-severity-calibration` owns this.
- **Whether the paper already answers it** — `tribunal-steelman-charity` owns this.
- **Whether the arithmetic is right** — `tribunal-evidence-recompute` owns this.
- **Whether the fix is safe to apply** — `tribunal-fix-safety` owns this.
- **Whether the defect is an extraction artifact** — `tribunal-substrate-artifact` owns this.

# Severity Guidance

`severity_revision` may only **lower** — lower when the valid core supports a weaker conclusion
than the finding states. An argument for raising is a `NOTE-TO-CHAIR:` line and is never
applied.

# Uncertainty Handling

`cant-tell` when the argument turns on a domain premise you cannot evaluate from the substrate
and docket — an identification assumption, a field convention, a proof step whose machinery is
absent. Give a resolvent naming what would settle it. `cant-tell` is **fail-closed** and never
counts toward upholding. Genuinely unsure an inference holds? The paper keeps the benefit of
the doubt.

# Output Contract

One row per finding: `{finding_id, angle: "logical-validity", verdict, severity_revision?,
note}`, `verdict ∈ upheld | upheld-with-revision | rejected | cant-tell`. `note` carries your
P1…Pn ⊢ C reconstruction compressed, and names the exact broken step. No confidence scores, no
run verdict — `tools/verdict.py` aggregates.

# Common Failure Modes

- Repairing the argument in your head, then upholding the repaired version.
- Accepting `INFERRED` without opening a single id in the chain.
- Confusing "the conclusion is true" with "the conclusion follows".
- Importing your own field knowledge as an unstated premise.

# Anti-Patterns

- Writing a philosophy essay instead of naming the broken step.
- Grading the finding's prose quality.
- Emitting `cant-tell` with no resolvent — that row is void and is re-run.
- Raising severity because the flaw makes the paper look worse.

# Example Invocation

> Run the verification angle at `panel/logical-validity/SKILL.md` over findings F-001..F-018.
> You are blind to the proposing seat and to other verifiers. Read-only — do not edit the
> substrate, docket, or findings. For each finding, reconstruct the argument as numbered
> premises, walk any `inference_chain` link by link against the ids it names, and test that the
> stated failure mode follows from the stated defect. One verdict row per finding; the run
> verdict belongs to `tools/verdict.py`. Emit findings per FINDING_SCHEMA.md. Do not write a
> verdict.

# Related Skills

- [tribunal-quote-locator](../quote-locator/SKILL.md) — settles whether the premise quote means what the argument needs.
- [tribunal-steelman-charity](../steelman-charity/SKILL.md) — kills valid arguments the paper has already pre-empted.
- [tribunal-evidence-recompute](../evidence-recompute/SKILL.md) — re-derives the numeric premises you take as given.
- [tribunal-severity-calibration](../severity-calibration/SKILL.md) — levels the conclusion that survives you.
- [tribunal-synthesis-chair](../../lanes/synthesis-chair/SKILL.md) — the only reader of your upward-severity notes.
