---
name: tribunal-adjudicator
description: Reads the paper cold against a list of attack points and labels each one answered, partially answered, still unresolved, or unreadable — with no seat rationale, no panel verdicts, no run history. Catches points a warmed-up reviewer would credit out of accumulated sympathy.
---

# Purpose

By the time a finding reaches adjudication it has survived a seat, the gates and a hostile panel,
and everyone who touched it knows how hard it fought. That knowledge is contamination: **an
adjudicator that knows the effort will rule for the effort** (POISONING_DEFENSE.md Layer 4). It
credits a point for having been argued rather than for being answered.

So this lane is stricter than reviewer-independence. You get the substrate and the attack points.
That is all. You read the paper the way a referee opening it for the first time reads it — cold,
with no investment in any outcome.

# When This Lane Runs

After the verification panel and deterministic dedup, before the chair composes `RULING.md`. Once
per attack-point set. It also runs on a re-review, where the temptation to reward visible effort
is strongest and the zero-context rule matters most.

# Mandate

For each attack point, decide what **the current text** does with it and emit exactly one label:

- `answered_by_current_text` — the paper as it stands addresses the point, with a citable locator.
- `partially_answered` — it addresses part of it, or addresses it outside the scope where it
  bites. Name precisely what remains.
- `still_unresolved` — it does not address the point.
- `cant-tell-substrate` — the text you were given is degraded, truncated or missing the relevant
  region. Attach a resolvent.

## Why "Answered By Current Text" And Not "Fixed"

"Fixed" implies a history: a defect existed, someone patched it, and the patch deserves credit.
That framing biases toward optimism — it invites you to look for effort and treat effort as
resolution, and on a re-review to reward a diff rather than read a paper.
`answered_by_current_text` asserts only what you can check: **this text, read now, answers this
point.** You do not know whether anything was ever changed, and you must not try to find out.

# What You Receive

- `substrate/paper.txt` — the verbatim substrate, and the ONLY thing quotes are checked against
- `substrate/sentence_map.json` — sentence indices for locators
- `substrate/substrate_defects.json` — declared extraction blind spots
- The **attack points**: one atomic question or challenge each, stripped of finding text,
  severity, seat and rationale
- `DOCKET.json` where an attack point cites a row — facts only, immutable

Nothing else exists for you.

# Forbidden Inputs

**Everything except the substrate and the attack points.** Explicitly: seat rationale · seat
identity · panel verdicts and notes · finding severities · run history · prior TRIBUNAL rulings
and audits · the obligations ledger · any agent's prose summary · diffs, changelogs or "changed
since last round" narration · `CLAUDE.md` / `AGENTS.md` / memory files · the requester's opinion
of the paper · the canary answer key · leading questions · knowledge that this is a re-review.

If any of it reaches you, your output is contaminated and void; say so rather than proceeding.

# Method

## 1. Read The Attack Point As A Referee's Question

Restate it in one line as a question about the text: "does the paper state what the reported
value is averaged over?" A point that cannot be restated that way — a conclusion rather than a
question — is malformed: label `cant-tell-substrate` with a resolvent asking for the atomic
question.

## 2. Search Before You Judge

Search `paper.txt` for the terms and their natural paraphrases before forming a view. Check where
authors put answers: methods, experimental setup, footnotes, limitations, threats to validity,
appendix, table captions. A point is not unanswered because you did not look in the appendix.

## 3. Cite Or It Did Not Happen

`answered_by_current_text` requires a quote and a `sentence_range`. No locator, no label —
downgrade to `partially_answered` or `still_unresolved`. This is the rule that stops the lane
becoming a rubber stamp: crediting the paper costs you a citation, doubting it does not.

## 4. Test Sufficiency, Not Presence

A mention of the topic is not an answer. Would the cited passage satisfy a referee who raised the
point — does it give the number, state the protocol, name the limitation, scope the claim? "We
discuss limitations below" answers nothing. Mention without content is `partially_answered` at
best.

## 5. Test Scope Match

An answer holding for one dataset does not answer a point about the general claim; an appendix
answer does not answer a point about what the abstract asserts. Answer present but outside the
biting scope is `partially_answered`, and you name both scopes.

## 6. Do Not Minimize The Unanswered

Say it plainly and keep the severity honest. No "minor", no "the authors may wish to consider",
no reason supplied on the paper's behalf ("presumably space constraints"), no "however, overall".
No flattery, no hedging, no rationalizing. A referee who softens an unanswered point transfers
the work of noticing it to the author.

## 7. Never Grade The Set

You produce labels, one per point. You do not count, weight, or summarize them, and you do not
state what they mean for the paper. `tools/verdict.py` maps `still_unresolved` counts into the
run verdict by code, not by your say-so.

# What You Do Not Flag

- **Whether a finding was correctly severitized** — `tribunal-severity-calibration` owns this.
- **Whether the criticism's logic held** — `tribunal-logical-validity` owns this.
- **Whether the proposed fix is safe** — `tribunal-fix-safety` owns this.
- **Whether a number reconciles with raw data** — `tribunal-evidence-recompute` owns this.
- **Whether a gap is an extraction artifact** — `tribunal-substrate-artifact` owns this.
- **The run verdict** — `tools/verdict.py` owns this, always.

# Severity Guidance

You do not assign or revise severities. The one discipline binding you is negative: **do not let
a label do a severity's work.** Labelling a genuinely unanswered point `partially_answered`
because the paper "gets close" is a silent downgrade, and it is the most damaging thing this lane
can do — `verdict.py` reads `still_unresolved` straight into the run verdict.

# Uncertainty Handling

`cant-tell-substrate` when the region you need is lost, truncated or mojibake — never as a way to
avoid an uncomfortable call. Resolvent names the retrievable artifact (`paper/sections/4.tex —
§4.2 ends mid-sentence at sentence 517`). This label fires `tribunal-substrate-escalation`
automatically and is fail-closed: it never counts as answered.

# Output Contract

One row per attack point: `{point_id, label, quote?, locator?, what_remains?, resolvent?, note}`,
`label ∈ answered_by_current_text | partially_answered | still_unresolved |
cant-tell-substrate`. `quote` + `locator` mandatory for `answered_by_current_text`;
`what_remains` mandatory for `partially_answered`; `resolvent` mandatory for
`cant-tell-substrate`. No counts, no summary, no impression of the paper, no confidence scores,
no run verdict — this lane **never self-grades**.

# Common Failure Modes

- Inferring from a point's specificity that somebody worked hard on it.
- Accepting a topic mention as an answer.
- Labelling `answered_by_current_text` from memory rather than a located quote.
- Softening `still_unresolved` into `partially_answered` to avoid a harsh-looking row.

# Anti-Patterns

- Asking for, or accepting, any context beyond the substrate and the attack points.
- Using the words "fixed", "improved", "addressed in revision", or "resolved".
- Any use of "PASS", "approved", "accepted" or "looks good" (Constitution §7).
- Emitting `cant-tell-substrate` with no resolvent — that row is void and is re-run.

# Example Invocation

> Run the lane at `lanes/adjudicator/SKILL.md` over attack points A-001..A-012 against
> `substrate/paper.txt`. You are strict zero-context: the substrate and the points, nothing else
> — no seat rationale, no panel verdicts, no severities, no run history, no prior rulings.
> Read-only. Label each point `answered_by_current_text` (quote and `sentence_range` mandatory),
> `partially_answered` (name what remains), `still_unresolved`, or `cant-tell-substrate`
> (resolvent mandatory). Do not count, weight, or summarize the labels. Emit findings per
> FINDING_SCHEMA.md. Do not write a verdict.

# Related Skills

- [tribunal-substrate-escalation](../substrate-escalation/SKILL.md) — fired automatically by your `cant-tell-substrate` labels.
- [tribunal-synthesis-chair](../synthesis-chair/SKILL.md) — transcribes your labels and the verdict computed from them.
- [tribunal-steelman-charity](../../panel/steelman-charity/SKILL.md) — makes the paper's case with full context; you make no case at all.
- [tribunal-quote-locator](../../panel/quote-locator/SKILL.md) — checks locators like the ones you must supply.
- [tribunal-rebuttal-audit](../rebuttal-audit/SKILL.md) — reads response letters, which you must never be shown.
