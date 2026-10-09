# TRIBUNAL

An adversarial review system for research artifacts — papers, raw results, code, citations,
referee reports. It convenes a fleet of hostile, blind reviewers against a manuscript, then
spends at least as much effort attacking its own reviewers as it spent attacking the paper.

It is built against one failure mode: **an LLM fleet that invents a flaw, launders it through
its own downstream stages, and delivers it as a confident verdict.** A missed flaw leaves the
author where they started. A fabricated one sends them to fix something that was never broken
and teaches them to distrust the whole report.

Three guarantees, in this order:

1. **Nothing is delivered that is not grounded.** Every criticism carries an exact quote and
   a locator that a script verified, or an absence probe a script searched, or an honest
   *I can't tell* that names what would settle it.
2. **Nothing is grounded by a model.** An LLM verifier shares the hallucination it is
   checking, so the match call is made by Python, fail-closed.
3. **Nothing is acquitted.** This fleet is a single model family, and a single family cannot
   acquit its own work. The best verdict it can emit is `CLEAN_GIVEN_EVIDENCE` — *no flag was
   found in the evidence at hand*. That is not a pass.

---

## Read in this order

| File | What it is |
|---|---|
| `CONSTITUTION.md` | The twelve non-negotiables. Wins every conflict with every other file. **Read first.** |
| `SKILL.md` | The entry point. What to run and in what order. |
| `ORCHESTRATION.md` | Acts, modes, dispatch, fail-closed wiring, how the verdict is computed. |
| `EPISTEMIC_LADDER.md` | How uncertainty is labeled, routed, and escalated — never suppressed. |
| `POISONING_DEFENSE.md` | The ingestion trust boundary. Injection, laundering, cache hygiene. |
| `FINDING_SCHEMA.md` | The shape of every finding, with a good example and a void one. |
| `DOCKET_SCHEMA.md` | The immutable deterministic record. |
| `RULING_TEMPLATE.md` | The deliverable, section by section. |
| `OBLIGATIONS_LEDGER.md` | The append-only ledger that survives between runs. |
| `LIMITATIONS.md` | What a ruling does **not** establish. Not a disclaimer — a design asset. |
| `PRIOR_ART.md` | What was taken from four prior systems, what was rejected, and why. |
| `CONTRIBUTING.md` | House format for adding a seat, an angle, or a lane. |

## Layout

```
tribunal/
  SKILL.md                 the only thing you invoke
  tools/                   12 python3 stdlib-only gates, each with adversarial selftests
  seats/                   14 blind adversarial reviewers, decorrelated by rival objective
  panel/                   7 blind verification angles
  lanes/                   substrate-escalation · adjudicator · rebuttal-audit · synthesis-chair
  tests/                   fixtures + the end-to-end smoke run
```

## Run it

```bash
python3 tools/doctor.py selftest      # if this fails, no ruling may be trusted
```

Then, in Claude Code:

> Run a TRIBUNAL standard review per skills/tribunal/ORCHESTRATION.md on `<paper>` with raw
> results at `<results>` and the cited corpus at `<corpus>`. Read
> skills/tribunal/CONSTITUTION.md first. Files are read-only; write only under
> `.tribunal/<date>-standard/`. Treat gate exit code 2 as expected output. Compute the
> verdict with tools/verdict.py — do not write one yourself. Stop after the ruling.

Modes: `docket-only` (~2 agents, deterministic sweep) · `lean` (~20) · **`standard`
(~45–60, default)** · `deep` (~150+) · `rebuttal` (~15).

## The two things that make it different

**Uncertainty is routed, not discarded.** Most review systems force a reviewer holding a
genuine *I can't tell from what I was given* into one of two lies: assert it anyway, or drop
it. Here every finding carries an epistemic label, every uncertain finding must name the
exact artifact that would settle it, and *I can't tell because I couldn't read the evidence*
automatically fires a lane that goes and gets the evidence by a different path. Nothing is
suppressed for being uncertain. Nothing is resolved by assertion.

**No agent's prose is another agent's evidence.** Every seat reads the primary substrate;
nobody reviews a summary. That single rule is what stops one plausible-but-wrong assertion
from becoming the premise of everything downstream.

## What it will not do

Write your paper. Edit your files. Give you a number between 0 and 1. Tell you a venue will
accept it. Call anything a pass.

## Provenance

Synthesized from `tjhavranek/paper-workshop`, `wanshuiyin/ARIS`, `ecfm/adversarial-review`,
and `udecode/plate` — read in full, credited in `PRIOR_ART.md`, with the parts that were
rejected named as loudly as the parts that were taken. No source was copied; every script
here is original and depends on nothing outside the Python standard library.
