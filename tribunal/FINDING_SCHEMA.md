# Finding Schema

One finding = one file at `.tribunal/<run-id>/findings/<id>.md`, plus one row in
`findings_ledger.json`. Every agent that emits findings emits **exactly this shape**. A finding that
does not validate is void and its seat is re-run.

---

# Frontmatter

```yaml
---
id: F-001                      # F-<3-digit>, unique within the run, never reused
title: <imperative, one line>  # "Report per-seed variance for Table 4", not "Issue with Table 4"
severity: High                 # High | Medium | Low — see rubric below. Tone-invariant.
epistemic: GROUNDED            # GROUNDED | INFERRED | SUSPECTED | CANT-TELL·SUBSTRATE
                               #   | CANT-TELL·COMPETENCE | CONTESTED  (EPISTEMIC_LADDER.md)
finding_class: numeric-mismatch
                               # see the controlled vocabulary below
artifact: paper                # paper | results | code | citations | referee-report | rebuttal
emitted_by: pedantic-statistician        # seat folder name
objective_function: find-the-fatal-flaw  # the seat's rival objective (ORCHESTRATION.md)

quote: "we observe a 15% improvement over the strongest baseline"
                               # EXACT substring of the substrate. Empty ONLY for absence classes.
locator:
  file: substrate/paper.txt
  section: "4.2 Main Results"
  sentence_range: [412, 413]   # indices into sentence_map.json — what locator_gate.py checks
  page: 7                      # if known; null otherwise. Never guessed.

absence_probe: []              # REQUIRED for absence classes: >=3 distinct terms + close
                               # paraphrases whose presence in the paper would REFUTE the claim
resolvent: null                # REQUIRED for CANT-TELL: the exact artifact/number/experiment
                               # that would settle it. Vague resolvents void the finding.
inference_chain: []            # REQUIRED for INFERRED: ids of the GROUNDED premises
why_unanchored: null           # REQUIRED for SUSPECTED: one sentence on what is missing
route_to: null                 # REQUIRED for CANT-TELL·COMPETENCE: the seat that should own it

gates:                         # filled by scripts, NEVER by an agent
  quote_gate: null             # matched | none | empty-quote | exempt-absence
  locator_gate: null           # in-span | out-of-span | no-map | exempt
  absence_gate: null           # absent | present | thin-probe | no-probe | not-absence-class
  evidence_check: null         # verified | value_not_found | path_missing | unparseable | n/a
docket_refs: []                # ids of DOCKET.json rows this finding rests on

panel: {}                      # filled by verdict.py from the verification panel
status: proposed               # proposed | delivered | rejected | contested | obligation
reject_reason: null            # required when status: rejected — never delete, always explain
corroborated_by: []            # seat names that independently raised the same defect
merged_from: []                # finding ids absorbed during deterministic dedup
---
```

# Body — required sections, in this order

```
# Evidence
# What is wrong
# Why it matters
# How it fails
# Proposed fix
# Risk of fix
# What would change my mind
```

- **Evidence** — the quote and locator restated in prose, plus the docket row if numeric. Reproducible
  by a human in under a minute or it is not evidence.
- **What is wrong** — the defect, stated as a defect, not as a feeling about the defect.
- **Why it matters** — the consequence for the paper's conclusions. "Style" is not a consequence.
- **How it fails** — the concrete failure mode: which claim breaks, which number is wrong, which
  reader is misled, what a replicator would find.
- **Proposed fix** — specific enough to act on without another conversation. A finding without a
  proposed fix is not a finding; it is a complaint.
- **Risk of fix** — what the proposed change could break. **A proposed edit that turns a correct
  passage wrong is itself a finding.** Every fix carries this field, and the `fix-safety` panel angle
  exists to attack it.
- **What would change my mind** — the falsification condition. Required for every finding at every
  epistemic level, not just uncertain ones. A finding you cannot imagine being wrong about is a
  belief, not an observation.

---

# Severity rubric — tone-invariant, three levels, no numbers

## `High`
Any one of these:
- A reported number does not reconcile with the raw evidence, in a direction that supports the paper.
- A central claim is unsupported by the presented evidence, or supported only outside its stated scope.
- The identification/inference strategy cannot support the causal or general claim being made.
- A result is not reproducible from the described procedure, or the described procedure is not the
  procedure the code implements.
- A cited work does not say what it is cited as saying, in a load-bearing position.
- A required baseline, ablation, control, or limitation is absent and its absence changes the reading.
- An integrity issue: undisclosed data exclusion, ground truth derived from model outputs without
  labeling, self-normalized scores, results claimed from files that do not exist.

## `Medium`
- A claim overreaches its evidence but the corrected claim survives.
- A secondary number, caption, or cross-reference is inconsistent.
- Missing statistical reporting (error bars, N, seeds, test choice) that a referee will demand.
- Related work omission that affects the novelty story but not the results.
- A structural or presentational defect that will predictably cause referee misreading.

## `Low`
- Wording that invites a misreading, without changing the claim.
- Formatting, cross-reference, notation, and consistency issues.
- Suggestions that would strengthen the paper but whose absence is not a defect.

## Rules
- **Severity describes the defect, never the reviewer's mood.** Reruns under different framing must
  produce identical severities (Constitution §5).
- **Maximum 7 `High` findings per run.** If you would name an eighth, downgrade something or record
  in the ruling why this artifact is exceptional. Severity inflation destroys the signal that makes a
  must-fix list worth reading.
- **Severity is orthogonal to epistemic status.** `High` + `CANT-TELL·SUBSTRATE` is legal, common, and
  usually the most important row in the ruling.
- **Never demote a finding for being unquotable.** Absence findings are quote-exempt by design.
- A panel may lower a severity. A panel may **not** raise one to make a finding survive; upward
  revision is recorded as a panel note for the chair, not applied silently.

---

# `finding_class` — controlled vocabulary

| Class | Quote required | Absence probe required |
|---|---|---|
| `numeric-mismatch` | yes | no |
| `statistical-inconsistency` | yes | no |
| `unsupported-claim` | yes | no |
| `scope-overclaim` | yes | no |
| `identification-failure` | yes | no |
| `method-code-divergence` | yes | no |
| `reproducibility-gap` | yes | no |
| `data-integrity` | yes | no |
| `citation-misuse` | yes | no |
| `prior-art-omission` | **no** | yes |
| `absence-silence` | **no** | yes |
| `contribution-undersell` | yes (foothold) | yes |
| `figure-table-mismatch` | yes | no |
| `ethics-dual-use` | yes | no |
| `presentation-defect` | yes | no |
| `substrate-defect` | no | no |
| `injection-artifact` | yes | no |
| `seat-failure` | no | no |

`substrate-defect` and `injection-artifact` are findings about the **evidence pipeline**, not the
paper, and are reported in their own section of the ruling so they are never confused with author
error. `seat-failure` is a meta-finding: a seat that padded, fabricated, or emitted resolventless
`CANT-TELL`s.

---

# Deterministic dedup

Findings are deduplicated by **code**, not by an agent's judgment, before any severity scoring:

- **Dedup key** = `finding_class` + normalized locator span overlap + normalized numeric token (when
  the class is numeric). Two findings whose sentence ranges overlap and whose class matches are
  candidates.
- Merge rules: title from the more specific/root-cause finding · quote and evidence are the **union** ·
  severity is the **higher** · `corroborated_by` is the union of seat names · `merged_from` records
  the absorbed ids.
- **Corroboration is reported, never used to down-weight.** Five blind seats independently finding the
  same defect is signal you want, not redundancy to penalize — *and* it is not five independent
  confirmations either, because they are the same model family (Constitution §7). The ruling prints
  the count and says exactly that.
- **Conflicting fixes do not merge.** Two findings citing the same evidence but proposing opposite
  changes become a single `decision_required` row on the board carrying both proposals.

---

# A good finding

```yaml
id: F-007
title: Reconcile the abstract's "15% improvement" with the 12.8% implied by Table 4
severity: High
epistemic: GROUNDED
finding_class: numeric-mismatch
artifact: paper
emitted_by: pedantic-statistician
objective_function: find-the-fatal-flaw
quote: "we observe a 15% improvement over the strongest baseline"
locator: {file: substrate/paper.txt, section: "Abstract", sentence_range: [4, 4], page: 1}
gates: {quote_gate: matched, locator_gate: in-span, evidence_check: verified}
docket_refs: [D-041, D-042]
```

> **Evidence** — Abstract, sentence 4: "we observe a 15% improvement over the strongest baseline."
> Table 4 (docket D-041, D-042) reports 85.3 for the method and 75.6 for the strongest baseline,
> both traced to `results/main_eval.json`. The relative improvement is (85.3−75.6)/75.6 = 12.8%.
>
> **What is wrong** — The abstract's headline number is not the number the results produce.
> **Why it matters** — It is the first and most-quoted number in the paper, and it overstates the
> contribution by roughly a sixth. **How it fails** — Any referee who recomputes it finds the
> discrepancy, and the recomputation takes ten seconds. **Proposed fix** — Replace "15%" with "12.8%"
> in the abstract and §1, or state the number as absolute points (+9.7). **Risk of fix** — If "15%"
> was computed against a different baseline than "strongest," changing the number without changing
> the comparator hides a second error; check which baseline was intended.
> **What would change my mind** — A results file showing a different pair of values for this
> comparison, or a stated definition of "improvement" other than relative gain.

# A bad finding — this is void, not merely weak

```yaml
id: F-099
title: Improve the methodology
severity: High
epistemic: GROUNDED
quote: "the methods section feels underspecified"
```

Four violations: the "quote" is the reviewer's own sentence and will fail the quote gate; the title
names no defect and no action; there is no locator, no evidence, no proposed fix, no falsification
condition; and `GROUNDED` is asserted with no gate result. This is conjecture wearing a finding's
frontmatter. Reject and re-emit against a specific span, or emit an honest `CANT-TELL` with a
resolvent.
