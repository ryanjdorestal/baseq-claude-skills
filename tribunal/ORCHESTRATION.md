# Orchestration — how a run is sequenced, and who is allowed to decide what

One run produces **one ruling**. Seats contribute findings; they do not produce their own
reports. Nothing is delivered that has not passed the gates and the panel.

---

# The five acts

```
ACT 0  CARTOGRAPHY   deterministic + 1 non-judging agent
       substrate.py build  →  paper.txt · sentence_map.json · evidence_manifest.json
                              substrate_defects.json
       injection_scan.py scan  →  injection_scan.json  (+ quarantined copies)
       précis agent (forbidden to judge)  →  precis.md
       ── NOTHING here reads a finding. NOTHING here forms an opinion. ──

ACT I  THE DOCKET    deterministic only — the run's only binding facts
       evidence_check.py batch      numeric claims → raw files
       stat_consistency.py batch    GRIM / GRIMMER / sd-range / percent / delta / p-values
       citation_gate.py check       existence + metadata (context is NOT checkable here)
       → DOCKET.json   immutable to every agent for the rest of the run

ACT II THE SEATS     N blind adversaries, commit-and-reveal
       each seat: substrate + docket + its jurisdiction, and NOTHING ELSE
       → findings_raw.json          (locked before any cross-talk)

ACT III GATES + PANEL
       quote_gate.py batch · absence_gate.py batch · locator_gate.py batch  → fail-closed
       verdict.py dedup             deterministic merge + corroboration counting
       7 blind panel angles × batches of ≤25          → panel_verdicts.json
       verdict.py panel             code-computed aggregation
       lanes/adjudicator            strict zero-context, per-point labels
       lanes/substrate-escalation   fired by every CANT-TELL·SUBSTRATE
       canary.py plant + score      measured sensitivity for THIS run
       verdict.py rule              the ruling's verdict — computed, never felt

ACT IV THE RULING
       lanes/synthesis-chair        transcribes; may not invent, merge, or re-severitize
       ledger.py sweep              opens obligations; flags disappearances
       → RULING.md · TRIBUNAL.json · findings/ · OBLIGATIONS.jsonl · SENSITIVITY.md
         MINORITY_REPORT.md · REJECTED_SUGGESTIONS.md

ACT V  REBUTTAL      optional; only when referee reports + a response letter are supplied
       lanes/rebuttal-audit
```

## Why this order

Cartography first because **no opinion may precede the evidence**. The docket second because
a deterministic fact must never be relitigated by a model — a seat that "disagrees" with a
docket row files a `substrate-defect` finding against the pipeline instead. Seats third,
blind, so their agreement means something. Gates before the panel so verifiers spend their
attention on semantics rather than on checking whether a quote is real. The adjudicator
late and cold, so it cannot be impressed by how hard a finding fought to get there. The
chair last, and powerless.

---

# Modes

| Mode | Seats | Panel angles | Canaries | Agents | Use |
|---|---|---|---|---|---|
| `docket-only` | 0 | 0 | 0 | ~2 | Deterministic sweep. Numbers, statistics, citations, injection. Minutes, near-free. |
| `lean` | 6 | 3 | 4 | ~20 | Fast read before circulating a draft. |
| **`standard`** (default) | 14 | 7 | 6 | ~45–60 | Pre-submission. Every seat, full panel, full escalation. |
| `deep` | 14 + close-reader sweeps | 7 × 2 redundant | 10 | ~150+ | Post-rejection forensics, high-stakes submission. |
| `rebuttal` | 4 + rebuttal lane | 3 | 0 | ~15 | Auditing a response letter against referee reports. |

`lean` seats: methodological-saboteur · pedantic-statistician · scope-police ·
data-integrity-forensic · steelman-defender · replication-engineer.
`lean` angles: quote-locator · steelman-charity · substrate-artifact.

`deep` adds close-reader sweeps: `ceil(sentences / 40)` agents, capped at 40, each owning a
contiguous span with no jurisdiction filter, to catch what a themed seat is not looking for.

**Mode never changes the rules.** Every gate, every fail-closed path, and every constitutional
rule is identical at `lean` and at `deep`. Mode buys coverage, not permission.

---

# Dispatch rules

1. **Seats are blind and parallel.** No seat sees another seat's output, the précis instead
   of the substrate, or the requester's opinion. Findings are locked before Act III begins.
2. **Different seats get different evidence diets.** The statistician gets the raw results
   tree; the historian gets the citation corpus; the figure seat gets the tables and captions.
   All get the substrate. Decorrelation is the point.
3. **A seat that finds nothing outputs `no_findings: true` and stops.** It does not invent
   work to look productive. This is recorded in the ruling as a clean jurisdiction.
4. **Cap: ~8 findings per seat.** More than that is padding, and padding is a
   constitutional violation (§3).
5. **Panel angles are blind to the proposer and to each other**, and judge at most 25
   findings per pass.
6. **Every seat and angle reads `CONSTITUTION.md` first.** An agent that has not read it is
   not authorized to emit a finding.

# Fail-closed wiring — the parts that are code, not prose

- A finding **no gate result covers** — a dropped or truncated relay row — is treated as
  unverified, exactly like a non-match. Never a silent keep of a seat's self-reported status.
- A finding **no panel angle covered** is `rejected`, not delivered (`verdict.py`).
- Any angle returning `rejected` kills the finding; `cant-tell` never counts toward upholding.
- The chair receives **only** delivered findings. A chair echoing a rejected id cannot
  resurrect it: `verdict.py` filters the id set before the chair runs, in code.
- The verified ledger is persisted **before** the chair runs, so a chair failure loses prose,
  never evidence.
- Any gate crash → `BLOCKED`. Never fail open, never "proceed with a note."

# Dedup and corroboration

Deterministic, in `verdict.py dedup`, before severity scoring: same `finding_class` +
overlapping sentence span, or an identical numeric token. Merged findings take the higher
severity, the union of evidence, and the union of `corroborated_by`.

**Corroboration is reported, never used to down-weight** — and never used to up-weight
either. Five blind Claude seats finding the same defect is worth printing, and it is *not*
five independent confirmations: they share a model family and therefore share priors. The
ruling prints the count and says exactly that.

Findings that cite the same evidence but propose **opposite fixes** do not merge. They
become one `decision_required` row carrying both proposals, for the author to settle.

# Escalation, interrupts, and stopping

- **`CANT-TELL·SUBSTRATE` → substrate-escalation lane**, automatically, max two rounds, then
  an open obligation. Never resolved by assertion.
- **STOP THE TRIBUNAL** — the only interrupt. A seat that finds a live-harm condition
  (exposed personal data in a public artifact, a safety-critical error in a deployed system,
  an undisclosed hazard in a released dataset) emits a single-line notice and halts further
  dispatch until the requester acknowledges. It is not a severity level; it is a fire alarm.
- **Deepening stops only when BOTH are true**: the most recent round produced zero new
  panel-passed High or Medium findings, **and** no jurisdiction reports uncovered ground.
  Low-severity items and typos can never keep the loop alive — on a same-family fleet, a
  naive "keep going until quiet" loop rewards manufacturing marginal false positives.
- **The One Forbidden Loop.** Never "revise → re-run → repeat until clean" (Constitution §12).
  Re-runs confirm a specific named discrepancy is gone. The **ledger**, not the verdict,
  decides whether the gate opens.

# The verdict, computed

`verdict.py rule` maps docket blocking conditions, delivered findings, adjudicator labels
and canary recall onto exactly one of:

`CLEAN_GIVEN_EVIDENCE` · `SOFT_FLAGS` · `HARD_FLAGS` · `BLOCKED` · `REVIEW_UNAVAILABLE` · `ERROR`

carrying `review_independence: same-family` and `acceptance_status: provisional`, always.
There is no `PASS` in the vocabulary and no agent may add one.

**Sensitivity gate:** if the fleet caught fewer than 60% of the planted canaries, the ruling
is stamped `LOW-SENSITIVITY`; at zero recall a quiet ruling becomes `REVIEW_UNAVAILABLE`,
because a fleet that cannot find defects someone deliberately planted has not demonstrated
it could find the author's.

---

# The single entry point

That prompt is the whole interface. Everything else lives in the skill files.

```
Run a TRIBUNAL <mode> review per skills/tribunal/ORCHESTRATION.md.

  paper:     <path to manuscript / .tex dir / PDF>
  results:   <path to raw results tree, or "none">
  corpus:    <path to cited-works corpus or .bib, or "none">
  referees:  <path to referee reports + response letter, or "none">
  out:       .tribunal/<YYYY-MM-DD>-<mode>/

Read skills/tribunal/CONSTITUTION.md before anything else; it binds every agent you spawn.

Constraints:
- Read-only on the author's files. Write only under `out`.
- Every finding cites an exact quote + locator, or an absence probe, or is an honest
  CANT-TELL with a resolvent. No exceptions, no confidence scores.
- Seats are blind and lock findings before cross-talk.
- Run the deterministic gates; treat exit code 2 as expected output, not an error.
- Compute the verdict with tools/verdict.py. Do not write one yourself.
- Stop after the ruling. No follow-up prose, no next-steps essay, no offer to fix the paper.
```
