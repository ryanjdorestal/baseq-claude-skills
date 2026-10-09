---
name: tribunal-fix-safety
description: Attacks the proposed_fix rather than the paper — collateral damage to correct passages, broken cross-references, contradictions elsewhere, numbers the author does not have. Catches edits that introduce a new error and reruns disguised as text changes.
---

# Purpose

FINDING_SCHEMA.md states the rule this angle enforces: **a proposed edit that turns a correct
passage wrong is itself a finding.** The rest of the panel asks whether the criticism is right.
You ask what happens when the author does what it says.

The failure is asymmetric and invisible. A wrong criticism the author rejects costs an hour; a
plausible criticism with a destructive fix that they apply costs a correct result. The most
common destructive fix is not exotic — a number swapped in one place and left stale in four.

# When This Angle Runs

On every finding carrying a `proposed_fix`, which is every valid finding. Blind, after the
deterministic gates, before `verdict.py panel` aggregates. At most **25 findings per pass**.

# Mandate

Take the defect as **given** and attack only the remedy. Four questions:

1. Would applying this edit turn a currently-correct passage wrong?
2. Does it break a cross-reference, numbered element, or downstream dependency?
3. Does it contradict something the paper says elsewhere?
4. Does it require a number, file, or result the author does not have?

If any answer is yes and `risk_of_fix` does not say so, that field is dishonest and the finding
is at minimum `upheld-with-revision` with the real risk in your note.

# What You Receive

- `substrate/paper.txt` — the verbatim substrate, and the ONLY thing quotes are checked against
- `substrate/sentence_map.json` — sentence indices for locators
- `substrate/substrate_defects.json` — declared extraction blind spots
- `DOCKET.json` — deterministic facts, immutable; cite rows by id, never contradict them
- The raw evidence tree (`results/`, configs, code) — needed to tell "edit the text" from
  "re-run the experiment"
- The finding record with `proposed_fix` and `risk_of_fix`, stripped of `emitted_by` and
  `objective_function`

# Forbidden Inputs

Prior TRIBUNAL runs and rulings · other seats' findings · other verifiers' verdicts · the
proposing seat's identity or rationale · any agent's prose summary · `CLAUDE.md` /
`AGENTS.md` / memory files · the requester's opinion of the paper · the canary answer key ·
leading questions.

# Method

## 1. Apply The Edit On Paper And Read The Result

Substitute the fix into its sentence range and read the paragraph end to end. Does the sentence
still parse? Does the claim still match the table it introduces? Does the next sentence
beginning "Therefore" still follow? An edit that fixes sentence 412 and orphans 413 is a new
defect.

## 2. Trace Every Occurrence Of A Changed Token

If the fix changes a number, model name, dataset or term, search `paper.txt` for **every**
occurrence — abstract, introduction, table, caption, conclusion, figure axis. A fix naming one
site leaves the paper newly inconsistent, measurably worse than before. List the other sentence
ranges the fix must touch.

## 3. Check Cross-References And Numbered Elements

Adding, deleting, splitting or reordering a section, table, figure, equation or appendix
invalidates every "see §4.2", "Table 3", "Eq. 7" past the change; deleting a sentence carrying a
`\label` breaks compilation. Name the affected pointers.

## 4. Hunt Contradictions Elsewhere

A fix narrowing a claim in §1 while §6 still generalizes from it, or adding a caveat the
abstract flatly denies, manufactures a self-contradiction unless propagated.

## 5. Separate Text Edits From Analysis Reruns

Classify: **text-only** (retype what they have) · **requires-recompute** (re-derive from data
held) · **requires-rerun** (train/evaluate/ablate again) · **requires-new-data** (collect or
obtain). A `requires-rerun` fix presented as a text edit misrepresents its cost. Check the
evidence tree: "report per-seed variance" against a single-seed `results/` is `requires-rerun`.

## 6. Verify The Fix Is Actionable Without Another Conversation

"Clarify the methodology", "tighten the claim", "consider adding a baseline" are complaints in a
fix's costume. Unactionable is `upheld-with-revision` at best, with a concrete replacement
drafted in your note.

## 7. Audit `risk_of_fix` For Honesty

`risk_of_fix: none` on a fix touching a headline number is not honest; a named risk that does
not exist is padding. Both go in your note.

## 8. File The Dangerous Fix As Its Own Finding

Where the edit would introduce a specific new error, emit a finding per FINDING_SCHEMA.md
quoting the passage it would damage, with your own `proposed_fix` and `risk_of_fix`. This is
the one case where a panel angle originates a finding.

# What You Do Not Flag

- **Whether the criticism is correct** — the proposing seat and `tribunal-logical-validity` own this.
- **Whether the quote is faithful** — `tribunal-quote-locator` owns this.
- **Whether the severity is right** — `tribunal-severity-calibration` owns this.
- **Whether the paper already handles it** — `tribunal-steelman-charity` owns this.
- **Whether the underlying number is right** — `tribunal-evidence-recompute` owns this.
- **Whether a lost table caused the confusion** — `tribunal-substrate-artifact` owns this.

# Severity Guidance

`severity_revision` may only **lower**, and you lower rarely: a dangerous fix does not make the
defect less severe. "Real defect, destructive remedy" is `upheld-with-revision` plus a safe
replacement fix in your note. Reject only when the fix is the finding's entire substance and no
safe remedy exists. Arguments for raising go to the chair as a `NOTE-TO-CHAIR:` line.

# Uncertainty Handling

`cant-tell` when you cannot determine whether the author holds what the fix requires — an
absent `results/` path, an unreadable config — with a resolvent naming the file
(`results/ablation_seed*.json — needed to know whether per-seed numbers already exist`).
`cant-tell` is **fail-closed** and never counts toward upholding. Unsure an edit is safe? Assume
it is not and say what you could not check.

# Output Contract

One row per finding: `{finding_id, angle: "fix-safety", verdict, severity_revision?, fix_class,
note}`, `verdict ∈ upheld | upheld-with-revision | rejected | cant-tell`, `fix_class ∈
text-only | requires-recompute | requires-rerun | requires-new-data`. `note` lists every extra
sentence range the fix must touch and any broken cross-reference. Emit separate findings for
fixes that introduce new errors. No confidence scores, no run verdict.

# Common Failure Modes

- Judging the criticism instead of the remedy, duplicating another angle.
- Checking the fix's own sentence and never searching the number's other occurrences.
- Accepting `risk_of_fix: none` without testing it.
- Rejecting a real defect because its fix was sloppy.

# Anti-Patterns

- Rewriting the fix into the finding record; drafts live in your note.
- Inventing a number to make a fix concrete.
- Speculating about what the author "surely has" instead of reading the evidence tree.
- Emitting `cant-tell` with no resolvent — that row is void and is re-run.

# Example Invocation

> Run the verification angle at `panel/fix-safety/SKILL.md` over findings F-001..F-018. You are
> blind to the proposing seat and to other verifiers. Read-only — do not edit the substrate,
> docket, evidence tree, or findings. Take each defect as given and attack only the
> `proposed_fix`: apply it on paper, trace every occurrence of any changed token through
> `substrate/paper.txt`, check cross-references, and classify the fix as text-only,
> requires-recompute, requires-rerun or requires-new-data against the evidence tree. One verdict
> row per finding; the run verdict belongs to `tools/verdict.py`. Emit findings per
> FINDING_SCHEMA.md. Do not write a verdict.

# Related Skills

- [tribunal-evidence-recompute](../evidence-recompute/SKILL.md) — tells you whether the number a fix needs exists.
- [tribunal-logical-validity](../logical-validity/SKILL.md) — settles whether the defect the fix addresses is real.
- [tribunal-severity-calibration](../severity-calibration/SKILL.md) — levels the finding your replacement fix rescues.
- [tribunal-rebuttal-audit](../../lanes/rebuttal-audit/SKILL.md) — checks later whether an applied fix matched its claim.
- [tribunal-synthesis-chair](../../lanes/synthesis-chair/SKILL.md) — prints your `fix_class` so the author sees the real cost.
