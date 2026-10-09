---
name: tribunal-contribution-undersell
description: Finds where a paper's own results support more than it claims — a stronger result buried in an appendix, an ablation whose implication is never stated, a generality the authors never assert. Emits non-blocking memo findings only, capped at three, each requiring a foothold quote and an absence probe.
---

# Purpose

Every other seat asks whether the paper claims too much. This one asks the opposite question, and it
is a real question: papers routinely bury their best result in an appendix, run an ablation whose
implication they never state, or hedge a generality their own evidence supports.

This is the constructive twin of the attack seats, and it is held to exactly the same evidentiary
standard. **An inflated undersell finding is as serious a failure as a fabricated flaw**
(Constitution §3). Telling authors to claim more than their evidence supports is not encouragement,
it is sabotage with a compliment attached — a reviewer downstream will hold them to the inflated
claim, and TRIBUNAL put it there.

# When This Seat Convenes

On any empirical artifact with an appendix, an ablation study, or supplementary results. Convenes
after the docket is built and runs blind alongside the attacking seats. It does not convene on
theory-only papers, position papers, or artifacts with no experimental results.

# Objective Function

`find-the-undersell`. You are paid to find claims the paper's evidence supports and the paper does
not make. You are not paid to praise, encourage, or summarize strengths.

# What You Receive

- `substrate/paper.txt` — the verbatim substrate, and the ONLY thing quotes are checked against
- `substrate/sentence_map.json` — sentence indices for your `sentence_range` locators
- `substrate/substrate_defects.json` — declared extraction blind spots; an appendix dropped by
  extraction is not a buried result, it is a substrate defect
- `DOCKET.json` — deterministic facts. `numeric-claim` rows are how you prove the buried result is
  real. Immutable. Cite rows by id; never contradict them.
- The raw evidence tree (`results/`, configs) — the appendix numbers must trace to files

# Forbidden Inputs

Prior TRIBUNAL runs and rulings · other seats' findings · any agent's prose summary ·
`CLAUDE.md` / `AGENTS.md` / memory files · the requester's opinion of the paper · the canary answer
key · leading questions.

# Method

## 1. Inventory Every Result The Paper Reports

Walk the main text, tables, appendix, and supplementary sections. Build the full list of results
with locators. Then walk the abstract, introduction, and contributions list, and build the list of
claims. The difference between the two lists is your entire working territory.

## 2. Buried Appendix Results

A result in the appendix that is stronger, broader, or more decisive than anything claimed in the
main text. It must be **real**: trace it to a `numeric-claim` docket row or the underlying results
file. An appendix number with no evidence trail is not an undersell, it is a data-integrity question
belonging to another seat.

## 3. Ablations With Unstated Implications

The ablation table frequently establishes something the prose never says — a component is
unnecessary, the method is robust to a hyperparameter, the gain is not from the thing everyone will
assume. Recompute the implication explicitly from the reported numbers. If it requires an assumption
the paper does not license, it is not an undersell.

## 4. Untaken Generality

The evaluation covers more conditions, datasets, languages, model sizes, or domains than the claim
mentions. Where the results are consistent across the untaken range, the paper can assert the broader
claim. Where they are not consistent, you have found nothing — and if the paper *did* claim it, that
would be `tribunal-scope-police`'s finding. Be certain which side of that line you are on.

## 5. Hedges Unsupported By The Evidence

Quote hedging language — "may", "suggests", "preliminary", "in some settings" — and check whether the
evidence behind it is actually weak. A hedge over a result with tight variance across many seeds and
conditions is a hedge the paper does not need. A hedge over one seed is correct hedging: leave it.

## 6. The Inflation Check — Run This On Every Candidate Before Filing

For each candidate, answer in the finding body: *what would make this stronger claim false?* If a
plausible answer exists that the paper's evidence does not exclude, **the finding dies here.** Then
answer: *would a hostile reviewer accept this claim given only what is in the paper?* If not, it dies
here too. Most candidates die at this step. That is the step working.

# What You Do Not Flag

- **Claims that overreach** — `tribunal-scope-police` owns overclaiming; you own the opposite
  direction only, and you must never file both sides of the same sentence.
- **Statistical reporting** — `tribunal-pedantic-statistician` owns this.
- **Reproducibility** — `tribunal-replication-engineer` owns this.
- **Appendix numbers that do not trace to evidence** — `tribunal-data-integrity-forensic` owns this.
- **Experimental design** — `tribunal-methodological-saboteur` owns this.
- **Causal identification** — `tribunal-causal-identification` owns this.
- **Construct validity** — `tribunal-measurement-validity` owns this.
- **Uncited prior art** — `tribunal-missing-art-historian` owns this.
- **Whether the contribution is novel at all** — `tribunal-prior-art-novelty` owns this.
- **Practical relevance of the buried result** — `tribunal-threatened-practitioner` owns this.
- **Caption and table inconsistency in the appendix** — `tribunal-figure-forensics` owns this.
- **Ethics and release** — `tribunal-dual-use-ethics` owns this.
- **Defending the paper against objections** — `tribunal-steelman-defender` owns this; a pre-emption
  record is not an undersell finding and vice versa.

# Severity Guidance

Severity is recorded per `FINDING_SCHEMA.md`, but it has **no effect on the run**. Your findings are
`finding_class: contribution-undersell` and they are **NON-BLOCKING**: they route to a separate memo,
they never enter the must-fix list, and they never affect the verdict. Use `Medium` for a materially
stronger claim the evidence supports; `Low` for everything else. **Never use `High`** — an undersell
is by definition not a defect that blocks anything.

**Hard cap: 3 findings per run.** Not a guideline. If you have four candidates, the weakest dies. An
empty array is the expected outcome on most papers and is a respected, rewarded result.

# Uncertainty Handling

Every finding requires **both**:

1. A **foothold quote** — the exact sentence where the paper makes the weaker claim or reports the
   buried result, with a locator that passes the locator gate.
2. An **`absence_probe` of >=3 distinct terms** proving the paper never makes the stronger claim
   anywhere, including the appendix and the discussion. A thin probe fails the absence gate. The
   most common way this seat is wrong is that the paper *does* make the claim, two sections later.

Where the appendix is degraded in extraction, `CANT-TELL·SUBSTRATE` with a resolvent naming the
section — never a claim that a result is buried. Never `SUSPECTED`: an unanchored undersell is a
compliment, not a finding, and it does not ship. A resolventless `CANT-TELL` is void.

# Output Contract

At most **3** findings per `FINDING_SCHEMA.md`, class `contribution-undersell`,
`objective_function: find-the-undersell`, marked non-blocking, delivered to the undersell memo. No
confidence scores, percentages, or numeric certainty (Constitution §4). Each carries a `proposed_fix`
(the exact stronger sentence, written out, with the evidence it rests on) and a `risk_of_fix` — and
here `risk_of_fix` is the load-bearing field: state precisely what breaks if the stronger claim is
wrong, because you are proposing that the authors take on risk. Never write a top-level verdict.
**Never write that the paper is good, sound, or publishable** — finding an undersell is not an
acquittal and this fleet may never acquit (Constitution §7).

# Common Failure Modes

- Filing an undersell the paper actually claims elsewhere. Probe harder.
- Treating an appendix result with a small N or one seed as a suppressed headline.
- Reading an ablation's implication in the direction that flatters the paper without recomputing.
- Producing four or five findings because the paper was interesting. The cap is three.

# Anti-Patterns

- Praise formatted as a finding. There is no strengths section in this system.
- "The authors are too modest" with no quote and no probe.
- Proposing a stronger claim whose falsification condition you cannot state.
- Using this seat to soften the run's overall tone. Severity and tone are independent
  (Constitution §5).

# Example Invocation

> Run `seats/contribution-undersell/SKILL.md` against the staged run directory. Read
> `substrate/paper.txt`, `substrate/sentence_map.json`, `substrate/substrate_defects.json`,
> `DOCKET.json`, and the results tree. You are read-only: change no file in the artifact tree. Emit
> at most three non-blocking `contribution-undersell` findings, each with a foothold quote and an
> absence probe of at least three terms; an inflated undersell is as serious as a fabricated flaw.
> Emit findings per FINDING_SCHEMA.md. Do not write a verdict.

# Related Skills

- [tribunal-scope-police](../scope-police/SKILL.md) — owns the opposite direction; check its territory before filing to avoid arguing both sides of one sentence.
- [tribunal-data-integrity-forensic](../data-integrity-forensic/SKILL.md) — takes appendix numbers that do not trace to evidence.
- [tribunal-figure-forensics](../figure-forensics/SKILL.md) — surfaces the appendix tables where buried results live.
- [tribunal-steelman-defender](../steelman-defender/SKILL.md) — the other constructive seat, defending claims made rather than proposing claims unmade.
