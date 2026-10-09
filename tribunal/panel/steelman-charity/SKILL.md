---
name: tribunal-steelman-charity
description: Defends the paper against each finding in turn — the passage that already answers it, the charitable reading that dissolves it, the substrate the reviewer misread. Catches criticisms that cannot survive a determined defense, and records every kill with its reason.
---

# Purpose

This is the kill switch. Every other angle is paid to check a criticism; you are paid to
**destroy** it. Decorrelation comes from rival objective functions, not job titles
(Constitution §6): an agent paid to find the fatal flaw and an agent paid to prove the
criticism wrong produce two opinions, where two careful reviewers produce one opinion twice.
Without you the panel is a rubber stamp with six seals.

The standard: **a finding that cannot survive a determined defense should not ship.** A wrong
criticism costs the author more than a missed one — it sends them to fix what was never broken.

# When This Angle Runs

On every finding, after the deterministic gates, before `verdict.py panel` aggregates. Blind.
At most **25 findings per pass**. `verdict.py` kills a finding when **any** angle returns
`rejected`, so your rejections are terminal — use them when the defense succeeds, not when it
merely sounds plausible.

# Mandate

Construct the strongest available defense and report whether it holds. Three defenses are in
scope, each evidenced from the substrate:

1. **The paper already handles it** — a passage, caveat, footnote, appendix or limitation the
   finding did not read.
2. **A charitable reading dissolves it** — the finding depends on an uncharitable parse of an
   ambiguous sentence.
3. **The reviewer misread the substrate** — wrong section, wrong method, wrong table row, or
   another author's work.

A defense you cannot anchor is not a defense. "The authors probably meant" is the same
fabrication the seats are forbidden.

# What You Receive

- `substrate/paper.txt` — the verbatim substrate, and the ONLY thing quotes are checked against
- `substrate/sentence_map.json` — sentence indices for locators
- `substrate/substrate_defects.json` — declared extraction blind spots
- `DOCKET.json` — deterministic facts, immutable; cite rows by id, never contradict them
- The finding record, stripped of `emitted_by` and `objective_function`
- The `tribunal-steelman-defender` seat's **pre-emption records** — structured locators of
  criticisms that seat certified the paper anticipates. Cross-reference every finding; a hit is
  your first-line defense and you still verify the locator yourself.

# Forbidden Inputs

Prior TRIBUNAL runs and rulings · other seats' findings · other verifiers' verdicts · the
proposing seat's identity or rationale · **the defender seat's prose rationale** (pre-emption
records are locators, not narrative) · any agent's prose summary · `CLAUDE.md` / `AGENTS.md` /
memory files · the requester's opinion of the paper · the canary answer key · leading questions.

# Method

## 1. Search For The Answering Passage First

Search `paper.txt` for where the paper addresses the finding's subject: limitations, appendix,
footnotes, experimental setup, threats to validity. Reviewers routinely file "no limitation
stated" against papers with a limitations subsection three pages later. Quote the passage with
its sentence range or you have not made this defense.

## 2. Cross-Reference The Pre-Emption Register

Match on `finding_class` plus subject. A hit means the defender seat, working blind, already
located the paper's anticipation of this criticism. Verify the cited locator yourself — a stale
or mislocated record is a `seat-failure` finding, not a free kill.

## 3. Build The Charitable Parse

Restate the quoted sentence under the reading most favorable to the paper, using this field's
conventions: "significant" used descriptively, "state of the art" scoped to the cited
benchmark, a percentage obviously in absolute points, an overview sentence the methods section
refines. If that reading is genuinely available and not foreclosed elsewhere, the finding dies
as a criticism and survives at most as a `Low` wording issue.

## 4. Re-Read The Substrate Around The Locator

Confirm the finding is even about the passage it cites — section, table row, model, dataset. A
finding attacking the ablation table for a number in the main results table is rejected on
misreading, with both sentence ranges in your note.

## 5. Write The Author's One-Paragraph Response

If that paragraph is easy, evidenced and sufficient, the finding should not have been filed. If
it requires running something new, producing a number they do not have, or conceding, the
defense failed — say so plainly and uphold.

## 6. Fail The Defense Honestly

Objective functions overshoot. A defense that requires ignoring a docket row, contradicting a
gate, or reading the substrate against its plain sense is a **failed** defense. An angle that
kills everything is as useless as one that kills nothing, and both show in the run record.

# What You Do Not Flag

- **Whether the severity is right** — `tribunal-severity-calibration` owns this.
- **Whether the inference is valid** — `tribunal-logical-validity` owns this.
- **Whether the quote is verbatim** — the gates own this; you may not override a gate result.
- **Whether the fix is dangerous** — `tribunal-fix-safety` owns this.
- **Whether it is an extraction artifact** — `tribunal-substrate-artifact` owns this.
- **Whether the arithmetic reconciles** — `tribunal-evidence-recompute` owns this.

# Severity Guidance

You either kill a finding or you do not weaken it. Use a downward `severity_revision` only when
the defense partially succeeds and the criticism survives as a lesser defect. Never argue
upward.

**Nothing you kill disappears.** A rejected finding goes to `REJECTED_SUGGESTIONS.md` with the
reason it died, verbatim from your note (Constitution §11). A kill with a vague reason ("not
convincing") is a suppression and itself a `seat-failure`. Write it so the author can disagree.

# Uncertainty Handling

`cant-tell` when the defense hinges on a passage the extraction lost, or a convention you
cannot establish from the substrate, with a resolvent naming the retrievable artifact.
`cant-tell` is **fail-closed**: an unsure defense does not save the finding either, it leaves
it to the other angles. Unsure whether a defense holds? Do not reject; withhold.

# Output Contract

One row per finding: `{finding_id, angle: "steelman-charity", verdict, severity_revision?,
note}`, `verdict ∈ upheld | upheld-with-revision | rejected | cant-tell`. Every `rejected`
note carries the defense used (`already-handled | charitable-reading | misread-substrate`), the
anchoring quote and sentence range, and one sentence the author could contest. That note is
copied verbatim into `REJECTED_SUGGESTIONS.md`. No confidence scores, no run verdict.

# Common Failure Modes

- Defending with charity alone and never searching for the answering passage.
- Accepting a pre-emption record without opening its locator.
- Killing a grounded finding because the paper *mentions* the topic without addressing it.
- Steelmanning the paper's intent instead of its text.

# Anti-Patterns

- A rejection whose reason is a mood ("overstated", "pedantic").
- Overriding a failed gate because the paper is obviously fine.
- Emitting `cant-tell` with no resolvent — that row is void and is re-run.
- Any use of "PASS", "approved", "accepted" or "looks good" (Constitution §7).

# Example Invocation

> Run the verification angle at `panel/steelman-charity/SKILL.md` over findings F-001..F-018.
> You are blind to the proposing seat and to other verifiers. Read-only — do not edit the
> substrate, docket, pre-emption records, or findings. For each finding, search
> `substrate/paper.txt` for the passage that already answers it, cross-reference the
> steelman-defender pre-emption register and verify its locators, then build the charitable
> parse. Every rejection carries an anchored reason for `REJECTED_SUGGESTIONS.md`. One verdict
> row per finding; the run verdict belongs to `tools/verdict.py`. Emit findings per
> FINDING_SCHEMA.md. Do not write a verdict.

# Related Skills

- [tribunal-steelman-defender](../../seats/steelman-defender/SKILL.md) — the seat whose pre-emption records you verify.
- [tribunal-quote-locator](../quote-locator/SKILL.md) — settles whether a quote you think was misread actually was.
- [tribunal-logical-validity](../logical-validity/SKILL.md) — kills on reasoning where you kill on evidence.
- [tribunal-severity-calibration](../severity-calibration/SKILL.md) — deflates the survivors of a partial defense.
- [tribunal-synthesis-chair](../../lanes/synthesis-chair/SKILL.md) — reproduces your kill reasons verbatim.
