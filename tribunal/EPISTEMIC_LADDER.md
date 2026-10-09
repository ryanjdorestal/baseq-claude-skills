# The Epistemic Ladder — how TRIBUNAL handles not knowing

Most review systems fail here. They offer one binary — flagged or not — and force a reviewer holding
a genuine "I can't tell from what I was given" into one of two lies: assert it anyway, or drop it.
`udecode/plate` instructs its reviewers to **suppress** anything below 0.50 confidence, which means
the highest-stakes unverifiable risks are exactly the ones that silently vanish.

TRIBUNAL does the opposite. **Uncertainty is a routed state, not a discarded one.** Every finding
carries an epistemic label, every uncertain finding carries a resolvent, and some uncertainties
trigger machinery instead of a shrug.

---

# The Ladder

Every finding carries exactly one `epistemic` label. Labels are words. **There are no numbers on this
ladder and there never will be** (Constitution §4).

| Label | Means | Requires |
|---|---|---|
| `GROUNDED` | An exact quote passed `quote_gate.py` **and** the locator passed `locator_gate.py`, or a numeric value matched raw data by token equality in `evidence_check.py`, or an absence claim was certified by `absence_gate.py` | Gate result id |
| `INFERRED` | Follows by stated reasoning from one or more `GROUNDED` facts | `inference_chain[]` naming each grounded premise by finding/docket id |
| `SUSPECTED` | A pattern-level suspicion with no anchor in the artifact. Real reviewers have these and they are often right | `why_unanchored` — one sentence on what is missing |
| `CANT-TELL · SUBSTRATE` | The reviewer cannot judge because **the input is degraded, absent, or unreadable** | `resolvent` + auto-escalation |
| `CANT-TELL · COMPETENCE` | The question is outside this seat's jurisdiction or expertise | `resolvent` + `route_to` |
| `CONTESTED` | The verification panel split; no majority | Both positions preserved verbatim |

## `GROUNDED` is not "true"

A `GROUNDED` label certifies **provenance, not correctness**. It says: this quote really is in the
paper, at the place claimed; this number really is in that file. It does not say the finding built on
it is right. A gate certifies the *search*, never the *semantics*.

## The two `CANT-TELL`s are different animals

This distinction is the one most systems collapse, and collapsing it is why their uncertain findings
rot:

- **`CANT-TELL · SUBSTRATE`** — *"I can't tell whether this is wrong, because I can't see the thing
  properly."* The PDF extraction dropped Table 3. The results file the paper cites isn't in the
  bundle. The equation came through as mojibake. The figure exists only as pixels and I am reading
  text. **This is a defect in the evidence pipeline, and it is fixable by going and getting the
  thing.** It is never the finding's fault and never the paper's fault until proven otherwise.
- **`CANT-TELL · COMPETENCE`** — *"I can see it fine; judging it isn't my seat."* A statistics seat
  looking at a domain-specific identification assumption. A methods seat looking at an ethics
  question. **This is a routing problem**, and the finding names the seat that should own it.

---

# The rules that make this robust rather than decorative

## 1. Uncertainty is rewarded, never penalized

No seat is scored on finding count, and no seat is scored on how confident it sounds. A seat that
returns two `GROUNDED` findings and four honest `CANT-TELL`s has done better work than a seat that
returns six confident guesses, and the ruling says so.

## 2. Every `CANT-TELL` must name its resolvent

A `CANT-TELL` without a **resolvent** is void and is re-run. The resolvent is the specific,
retrievable thing that would settle the question:

> **Valid:** `resolvent: "results/ablation_seed*.json — need per-seed accuracy for Table 4 row 3;
> the paper reports a single number and does not say whether it is mean or best."`
>
> **Void:** `resolvent: "more information about the experiments."`

This one rule is what stops `CANT-TELL` from becoming a productivity dodge. Naming what would settle
a question is hard, and an agent that cannot name it usually did not have a real question.

## 3. `CANT-TELL · SUBSTRATE` fires the escalation lane automatically

The reviewer does not get to shrug and move on, and the orchestrator does not get to bury it. The
lane in `lanes/substrate-escalation/SKILL.md` runs:

1. **Re-acquire the artifact by a different path.** Text extraction failed → re-extract with layout
   preserved, or read the `.tex`/`.docx` source, or open the raw CSV/JSON directly, or hash-check the
   file and report it missing. *Never re-ask the same agent to try harder on the same substrate.*
2. **Re-pose the single question** to a fresh zero-context agent, with the new substrate and nothing
   else — no prior rationale, no seat framing, no leading question.
3. **At most two escalations.** Then it becomes an **open obligation** on `OBLIGATIONS.jsonl`,
   printed in the ruling under *Unresolved — evidence not obtainable*, with its resolvent attached so
   the author knows exactly what to hand over.

It is never resolved by assertion. It is never quietly dropped. If TRIBUNAL could not see something,
the deliverable says which thing, and why, and what would fix it.

## 4. Suppression is banned

Nothing is deleted for being uncertain. Findings change lane, they do not evaporate. Findings killed
by the panel go to `REJECTED_SUGGESTIONS.md` **with the reason** — a killed finding with a recorded
reason is information; a silently dropped one is a lie of omission.

## 5. Severity and epistemic status are orthogonal axes

A finding may be **`High` severity and `CANT-TELL · SUBSTRATE` at the same time**, and that
combination is often the most important row in the entire ruling: *something load-bearing may be
wrong and we could not check it.* Surface it loudly **and** flag it unconfirmed.

**Nothing is ever demoted for being unquotable.** The worst problems in a paper are usually things it
never says: the missing baseline, the unreported ablation, the absent limitation, the caveat that was
in the preprint and isn't in the submission. Absence findings are quote-exempt by design and ride the
absence gate instead.

## 6. The inflation guard runs in both directions

- A seat whose findings are mostly `SUSPECTED` with no anchors is flagged **speculative** and its
  jurisdiction is re-run with a stricter grounding demand.
- A seat whose findings are mostly `CANT-TELL` **without resolvents** is flagged **degraded** and
  re-run. Uncertainty is free; unresolvable uncertainty is not.
- A seat that returns nothing is flagged **clean** and nothing happens to it. That is a normal,
  healthy outcome and the ruling records it as such.

## 7. `CONTESTED` is preserved, not averaged

When the verification panel splits, the finding does not get a mean score — it gets the label
`CONTESTED`, both positions verbatim, and a line in the minority report. Averaging disagreement
between correlated same-family agents manufactures a false consensus out of a real dispute.

---

# How labels flow into the ruling

| Label | Where it lands in `RULING.md` |
|---|---|
| `GROUNDED` + High/Medium | Must-fix table, with quote and locator |
| `GROUNDED` + Low | Minor issues list |
| `INFERRED` | Must-fix or minor, with the inference chain printed so the author can attack it |
| `SUSPECTED` | *Unanchored concerns — check these yourself* section, explicitly marked as not evidence |
| `CANT-TELL · SUBSTRATE` (post-escalation) | *Unresolved — evidence not obtainable*, with resolvent |
| `CANT-TELL · COMPETENCE` (unrouted) | *Unrouted questions*, with the seat that should own it |
| `CONTESTED` | Must-fix table if High, always also in the minority report |

Nothing on this ladder is invisible in the deliverable. If TRIBUNAL thought it, the author sees it,
correctly labeled, exactly once.
